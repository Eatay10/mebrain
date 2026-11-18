"""Güvenlik olayları ve alarm kuralları — knowledge OBSERVABILITY.md §5–§6."""

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, literal, select, text
from sqlalchemy.orm import Session

from app import contract as c
from app.auth.policies import can_read_security, require
from app.core.schemas import PageParams, user_ref
from app.models import SecurityEvent, User
from app.models.base import utcnow

WINDOWS = {
    "1h": (timedelta(hours=1), "5 minutes"),
    "24h": (timedelta(hours=24), "1 hour"),
    "7d": (timedelta(days=7), "6 hours"),
}
EPOCH = datetime(2000, 1, 1, tzinfo=UTC)


def _event(e: SecurityEvent) -> c.SecurityEvent:
    return c.SecurityEvent(
        id=e.id,
        occurred_at=e.occurred_at,
        type=e.type,
        severity=e.severity,
        user=user_ref(e.user),
        ip=str(e.ip) if e.ip else None,
        request_id=e.request_id,
        details=e.details,
    )


def list_events(
    db: Session,
    user: User,
    pp: PageParams,
    etype: str | None,
    severity: str | None,
    frm: datetime | None,
    to: datetime | None,
) -> c.SecurityEventPage:
    require(can_read_security(user), user, "security.read")
    q = select(SecurityEvent)
    if etype:
        q = q.where(SecurityEvent.type == etype)
    if severity:
        q = q.where(SecurityEvent.severity == severity)
    if frm:
        q = q.where(SecurityEvent.occurred_at >= frm)
    if to:
        q = q.where(SecurityEvent.occurred_at <= to)
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    rows = db.scalars(
        q.order_by(SecurityEvent.occurred_at.desc(), SecurityEvent.id.desc())
        .offset(pp.offset)
        .limit(pp.page_size)
    ).unique()
    return c.SecurityEventPage(
        items=[_event(e) for e in rows], total=total, page=pp.page, page_size=pp.page_size
    )


def _bucket(interval: str) -> Any:
    return func.date_bin(text(f"interval '{interval}'"), SecurityEvent.occurred_at, literal(EPOCH))


def _burst(
    db: Session,
    since: datetime,
    types: list[str],
    key: Any,
    interval: str,
    threshold: int,
    rule: str,
    severity: str,
    label: str,
) -> list[c.OpenAlert]:
    b = _bucket(interval).label("b")
    q = (
        select(key.label("k"), b, func.count().label("n"), func.min(SecurityEvent.occurred_at).label("first"))
        .where(SecurityEvent.occurred_at >= since, SecurityEvent.type.in_(types), key.is_not(None))
        .group_by(key, b)
        .having(func.count() >= threshold)
    )
    agg: dict[str, c.OpenAlert] = {}
    for row in db.execute(q):
        k = str(row.k)
        prev = agg.get(k)
        if prev is None:
            agg[k] = c.OpenAlert(
                rule=rule, severity=severity, first_seen=row.first, count=row.n, sample=f"{label}: {k}"
            )
        else:
            prev.count += row.n
            prev.first_seen = min(prev.first_seen, row.first)
    return list(agg.values())


def _user_labels(db: Session, alerts: list[c.OpenAlert]) -> None:
    for a in alerts:
        if a.sample and a.sample.startswith("Kullanıcı: "):
            u = db.get(User, a.sample.removeprefix("Kullanıcı: "))
            if u:
                a.sample = f"Kullanıcı: {u.full_name}"


def alerts(db: Session, since: datetime) -> list[c.OpenAlert]:
    out: list[c.OpenAlert] = []
    out += _burst(db, since, ["LOGIN_FAILED"], SecurityEvent.ip, "1 minute", 5, "brute_force", "HIGH", "IP")
    out += _burst(
        db,
        since,
        ["AUTHZ_DENIED", "NOT_FOUND_PROBE"],
        SecurityEvent.user_id,
        "5 minutes",
        10,
        "authz_burst",
        "HIGH",
        "Kullanıcı",
    )
    out += _burst(
        db, since, ["API_TOKEN_INVALID"], SecurityEvent.ip, "5 minutes", 10, "token_abuse", "HIGH", "IP"
    )
    out += _burst(
        db, since, ["BULK_EXPORT"], SecurityEvent.user_id, "1 hour", 5, "mass_export", "MEDIUM", "Kullanıcı"
    )
    locked = db.execute(
        select(func.count(), func.min(SecurityEvent.occurred_at)).where(
            SecurityEvent.occurred_at >= since, SecurityEvent.type == "ACCOUNT_LOCKED"
        )
    ).one()
    if locked[0]:
        out.append(
            c.OpenAlert(
                rule="account_lockout", severity="MEDIUM", first_seen=locked[1], count=locked[0], sample=None
            )
        )
    priv = db.execute(
        select(func.count(), func.min(SecurityEvent.occurred_at)).where(
            SecurityEvent.occurred_at >= since,
            SecurityEvent.type == "ROLE_CHANGED",
            SecurityEvent.details["to"].astext.in_(["DIRECTOR", "AUDITOR"]),
        )
    ).one()
    if priv[0]:
        out.append(
            c.OpenAlert(
                rule="privilege_change",
                severity="HIGH",
                first_seen=priv[1],
                count=priv[0],
                sample="Yüksek yetkili rol atandı",
            )
        )
    _user_labels(db, out)
    order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "INFO": 3}
    return sorted(out, key=lambda a: (order.get(str(getattr(a.severity, "value", a.severity)), 9), -a.count))


def summary(db: Session, user: User, window: str) -> c.SecuritySummary:
    require(can_read_security(user), user, "security.read")
    span, interval = WINDOWS[window]
    since = utcnow() - span
    counts = dict(
        db.execute(
            select(SecurityEvent.type, func.count())
            .where(SecurityEvent.occurred_at >= since)
            .group_by(SecurityEvent.type)
        ).all()
    )
    b = _bucket(interval).label("b")
    timeline: dict[datetime, dict[str, int]] = {}
    for row in db.execute(
        select(b, SecurityEvent.type, func.count())
        .where(SecurityEvent.occurred_at >= since, SecurityEvent.severity != "INFO")
        .group_by(b, SecurityEvent.type)
    ):
        timeline.setdefault(row[0], {})[row[1]] = row[2]
    sources = db.execute(
        select(SecurityEvent.ip, func.count(), func.max(SecurityEvent.occurred_at))
        .where(
            SecurityEvent.occurred_at >= since,
            SecurityEvent.severity != "INFO",
            SecurityEvent.ip.is_not(None),
        )
        .group_by(SecurityEvent.ip)
        .order_by(func.count().desc())
        .limit(10)
    ).all()
    return c.SecuritySummary(
        window=window,
        counts_by_type=counts,
        timeline=[
            c.TimelineItem(bucket=k, count=sum(v.values()), by_type=v) for k, v in sorted(timeline.items())
        ],
        top_sources=[c.TopSource(ip=str(ip), count=n, last_seen=last) for ip, n, last in sources],
        open_alerts=alerts(db, since),
    )
