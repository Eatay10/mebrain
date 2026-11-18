"""Planlı raporlar (haftalık/aylık).

Rapor, plan sahibinin yetki kapsamıyla üretilir ve CSV olarak e-postalanır.

Zamanlama (Europe/Istanbul): haftalık → pazartesi 08:00 (önceki 7 gün), aylık → ayın 1'i 08:00 (önceki ay).
"""

import csv
import io
from datetime import date, datetime, time, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import contract as c
from app.audit.service import record
from app.auth import policies as P
from app.auth.scope import in_scope, visible_team_ids
from app.contract import NotificationType as NT
from app.contract import ReportFrequency as RF
from app.core.csv_export import safe_cell
from app.core.errors import NotFound
from app.core.logging import log
from app.models import ReportSchedule, User
from app.models.base import utcnow
from app.modules.notifications.service import notify
from app.modules.reports import service as reports

TZ = ZoneInfo("Europe/Istanbul")
RUN_AT = time(8, 0)
GROUP_TR = {
    "unit": "unit",
    "team": "ekip",
    "assignee": "kişi",
    "project": "proje",
    "status": "durum",
    "priority": "öncelik",
    "category": "kategori",
    "type": "tür",
}


def next_run(freq: RF, after: datetime) -> datetime:
    local = after.astimezone(TZ)
    if freq == RF.WEEKLY:
        days = (7 - local.weekday()) % 7  # bir sonraki pazartesi
        candidate = datetime.combine(local.date() + timedelta(days=days), RUN_AT, TZ)
        if candidate <= local:
            candidate += timedelta(days=7)
    else:
        first = local.date().replace(day=1)
        candidate = datetime.combine(first, RUN_AT, TZ)
        if candidate <= local:
            nxt = (first + timedelta(days=32)).replace(day=1)
            candidate = datetime.combine(nxt, RUN_AT, TZ)
    return candidate


def period(freq: RF, run_at: datetime) -> tuple[date, date]:
    d = run_at.astimezone(TZ).date()
    if freq == RF.WEEKLY:
        return d - timedelta(days=7), d - timedelta(days=1)
    last = d.replace(day=1) - timedelta(days=1)
    return last.replace(day=1), last


def to_contract(s: ReportSchedule) -> c.ReportSchedule:
    return c.ReportSchedule(
        id=s.id,
        name=s.name,
        frequency=s.frequency,
        group_by=s.group_by,
        team_id=s.team_id,
        active=s.active,
        next_run_at=s.next_run_at,
        last_run_at=s.last_run_at,
        last_status=s.last_status,
        created_at=s.created_at,
    )


def _own(db: Session, user: User, schedule_id: UUID) -> ReportSchedule:
    s = db.get(ReportSchedule, schedule_id)
    if s is None or s.owner_id != user.id:
        raise NotFound("Rapor planı bulunamadı.")
    return s


def list_mine(db: Session, user: User) -> list[c.ReportSchedule]:
    rows = db.scalars(
        select(ReportSchedule).where(ReportSchedule.owner_id == user.id).order_by(ReportSchedule.created_at)
    )
    return [to_contract(s) for s in rows.unique()]


def create(db: Session, user: User, body: c.ReportScheduleCreate) -> c.ReportSchedule:
    P.require(P.can_schedule_reports(user), user, "report_schedule.create")
    if body.team_id is not None and not in_scope(body.team_id, visible_team_ids(db, user)):
        raise NotFound("Ekip bulunamadı.")
    s = ReportSchedule(
        owner_id=user.id,
        name=body.name.strip(),
        frequency=body.frequency,
        group_by=body.group_by.value,
        team_id=body.team_id,
        next_run_at=next_run(body.frequency, utcnow()),
    )
    db.add(s)
    db.flush()
    record(db, "report_schedule.create", "report_schedule", s.id, {"name": [None, s.name]})
    db.refresh(s)
    return to_contract(s)


def update(db: Session, user: User, schedule_id: UUID, body: c.ReportScheduleUpdate) -> c.ReportSchedule:
    s = _own(db, user, schedule_id)
    for name in body.model_fields_set:
        value = getattr(body, name)
        if value is None:
            continue
        setattr(s, name, value.value if name == "group_by" else value)
    if {"frequency", "active"} & body.model_fields_set:
        s.next_run_at = next_run(s.frequency, utcnow())
    record(
        db,
        "report_schedule.update",
        "report_schedule",
        s.id,
        {"fields": [None, sorted(body.model_fields_set)]},
    )
    db.flush()
    db.refresh(s)
    return to_contract(s)


def delete(db: Session, user: User, schedule_id: UUID) -> None:
    s = _own(db, user, schedule_id)
    record(db, "report_schedule.delete", "report_schedule", s.id, {"name": [s.name, None]})
    db.delete(s)


def _csv(rows: list[list[object]]) -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\r\n")
    for row in rows:
        writer.writerow([safe_cell(v) for v in row])
    return ("﻿" + buf.getvalue()).encode()


def execute(db: Session, s: ReportSchedule, now: datetime) -> bool:
    """Raporu üretip sahibine e-postalar; başarı durumunu ve bir sonraki çalışmayı kaydeder."""
    from app.email.sender import send

    frm, to = period(s.frequency, now)
    owner = s.owner
    ok = True
    try:
        if not owner.is_active:
            raise PermissionError("owner inactive")
        report = reports.build(db, owner, s.group_by, frm, to, s.team_id, None)
        data = _csv(reports.csv_rows(db, owner, report))
        label = "Haftalık" if s.frequency == RF.WEEKLY else "Aylık"
        t = report.totals
        group = GROUP_TR.get(s.group_by, s.group_by)
        body = (
            f"{label} rapor: {s.name}\n{frm:%d.%m.%Y} – {to:%d.%m.%Y}, {group} bazında. "
            f"Toplam {t.total} task; tamamlanan {t.done}, geciken {t.overdue}."
        )
        send(
            owner.email,
            f"{label} rapor: {s.name}",
            body,
            "/reports",
            attachments=[(f"rapor-{s.group_by}-{frm}-{to}.csv", "text/csv", data)],
        )
        notify(
            db,
            [owner.id],
            NT.REPORT_READY,
            f"{label} rapor gönderildi: {s.name}",
            body=body,
            entity_type="report_schedule",
            entity_id=s.id,
            email=False,
        )
    except Exception as exc:  # noqa: BLE001 — iş tekrar denenecek
        ok = False
        log.warning("report_schedule_failed", schedule=str(s.id), error_type=type(exc).__name__)
    s.last_run_at = now
    s.last_status = "SUCCESS" if ok else "FAILED"
    s.next_run_at = next_run(s.frequency, now)
    return ok


def run_now(db: Session, user: User, schedule_id: UUID) -> None:
    s = _own(db, user, schedule_id)
    nxt = s.next_run_at
    execute(db, s, utcnow())
    s.next_run_at = nxt  # elle çalıştırma takvimi kaydırmaz


def run_due(db: Session) -> int:
    now = utcnow()
    due = list(
        db.scalars(
            select(ReportSchedule)
            .where(ReportSchedule.active.is_(True), ReportSchedule.next_run_at <= now)
            .with_for_update(skip_locked=True, of=ReportSchedule)
        ).unique()
    )
    return sum(1 for s in due if execute(db, s, now))
