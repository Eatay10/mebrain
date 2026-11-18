"""Toplu task raporu (RPT-01/02). Tarih filtresi task'ın oluşturulma tarihine göre."""

from datetime import date, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import contract as c
from app.audit.service import record
from app.auth.scope import in_scope, team_filter, visible_team_ids
from app.core.errors import BadRequest, NotFound
from app.models import Project, Task, Team, User
from app.modules.tasks import counting
from app.security_events.service import emit

GROUP_COLUMNS: dict[str, Any] = {
    "team": Task.team_id,
    "assignee": Task.assignee_id,
    "project": Task.project_id,
    "status": Task.status,
    "priority": Task.priority,
    "category": Task.category,
    "type": Task.type,
}
MAX_RANGE_DAYS = 366


def _labels(db: Session, group_by: str, keys: list[Any]) -> dict[Any, str]:
    ids = [k for k in keys if k is not None]
    if group_by == "team":
        return {t.id: t.name for t in db.scalars(select(Team).where(Team.id.in_(ids))).unique()}
    if group_by == "assignee":
        return {u.id: u.full_name for u in db.scalars(select(User).where(User.id.in_(ids))).unique()}
    if group_by == "project":
        return {p.id: p.name for p in db.scalars(select(Project).where(Project.id.in_(ids))).unique()}
    return {k: getattr(k, "value", str(k)) for k in ids}


def build(
    db: Session, user: User, group_by: str, frm: date, to: date, team_id: UUID | None, project_id: UUID | None
) -> c.TaskReport:
    if to < frm:
        raise BadRequest(errors=[{"field": "to", "message": "Bitiş başlangıçtan önce olamaz."}])
    if (to - frm).days > MAX_RANGE_DAYS:
        raise BadRequest(
            errors=[{"field": "to", "message": f"Aralık en fazla {MAX_RANGE_DAYS} gün olabilir."}]
        )
    scope = visible_team_ids(db, user)
    if team_id is not None and not in_scope(team_id, scope):
        raise NotFound("Ekip bulunamadı.")
    where = [
        team_filter(Task.team_id, scope),
        Task.created_at >= frm,
        Task.created_at < to + timedelta(days=1),
    ]
    if team_id:
        where.append(Task.team_id == team_id)
    if project_id:
        where.append(Task.project_id == project_id)
    col = GROUP_COLUMNS[group_by]
    by = counting.counts_by(db, [col], where)
    hours = func.avg(func.extract("epoch", Task.completed_at - Task.created_at) / 3600)
    avg = dict(
        db.execute(
            select(col, hours)
            .where(counting.live_task_filter(), Task.completed_at.is_not(None), *where)
            .group_by(col)
        ).all()
    )
    labels = _labels(db, group_by, [k[0] for k in by])
    rows = sorted(
        (
            c.Row(
                key=str(getattr(k[0], "value", k[0]) or "none"),
                label=labels.get(k[0], "Atanmamış"),
                counts=v,
                avg_completion_hours=round(float(avg[k[0]]), 1) if avg.get(k[0]) is not None else None,
            )
            for k, v in by.items()
        ),
        key=lambda r: (-r.counts.total, r.label),
    )
    totals = counting.empty()
    for r in rows:
        totals = counting.add(totals, r.counts)
    return c.TaskReport(group_by=group_by, **{"from": frm}, to=to, rows=rows, totals=totals)


def csv_rows(db: Session, user: User, report: c.TaskReport) -> list[list[object]]:
    record(db, "report.export", "report", None, {"groupBy": [None, report.group_by]})
    emit("BULK_EXPORT", user_id=user.id, details={"kind": "task_report", "groupBy": report.group_by})
    header = [
        "grup",
        "başlanmadı",
        "devam_ediyor",
        "bloklu",
        "tamamlandı",
        "gecikmiş",
        "toplam",
        "ort_tamamlanma_saat",
    ]
    body = [
        [
            r.label,
            r.counts.todo,
            r.counts.in_progress,
            r.counts.blocked,
            r.counts.done,
            r.counts.overdue,
            r.counts.total,
            r.avg_completion_hours if r.avg_completion_hours is not None else "",
        ]
        for r in report.rows
    ]
    t = report.totals
    return [header, *body, ["TOPLAM", t.todo, t.in_progress, t.blocked, t.done, t.overdue, t.total, ""]]
