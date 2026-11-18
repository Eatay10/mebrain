"""Audit kayıtlarını okuma (yönetici: yönettiği ekip üyelerinin işlemleri; direktör/denetmen: tümü)."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app import contract as c
from app.audit.service import record
from app.auth.policies import can_read_audit, require
from app.auth.scope import managed_team_ids, team_filter
from app.core.schemas import PageParams, user_ref
from app.models import AuditLog, User
from app.security_events.service import emit


def to_contract(r: AuditLog) -> c.AuditLogEntry:
    return c.AuditLogEntry(
        id=r.id,
        occurred_at=r.occurred_at,
        actor=user_ref(r.actor),
        actor_type=r.actor_type,
        action=r.action,
        entity_type=r.entity_type,
        entity_id=r.entity_id,
        changes=r.changes,
        ip=str(r.ip) if r.ip else None,
        request_id=r.request_id,
        result=r.result,
    )


def query(
    db: Session,
    user: User,
    actor_id: UUID | None,
    action: str | None,
    entity_type: str | None,
    entity_id: UUID | None,
    frm: datetime | None,
    to: datetime | None,
) -> Select[tuple[AuditLog]]:
    require(can_read_audit(user), user, "audit.read")
    q = select(AuditLog)
    scope = managed_team_ids(db, user) if user.role == c.Role.MANAGER else None
    if scope is not None:
        q = q.join(User, AuditLog.actor_id == User.id).where(team_filter(User.team_id, scope))
    if actor_id is not None:
        q = q.where(AuditLog.actor_id == actor_id)
    if action is not None:
        q = q.where(AuditLog.action == action)
    if entity_type is not None:
        q = q.where(AuditLog.entity_type == entity_type)
    if entity_id is not None:
        q = q.where(AuditLog.entity_id == entity_id)
    if frm is not None:
        q = q.where(AuditLog.occurred_at >= frm)
    if to is not None:
        q = q.where(AuditLog.occurred_at <= to)
    return q.order_by(AuditLog.occurred_at.desc(), AuditLog.id.desc())


def page(db: Session, q: Select[tuple[AuditLog]], pp: PageParams) -> c.AuditLogPage:
    total = db.scalar(select(func.count()).select_from(q.order_by(None).subquery())) or 0
    rows = db.scalars(q.offset(pp.offset).limit(pp.page_size)).unique()
    return c.AuditLogPage(
        items=[to_contract(r) for r in rows], total=total, page=pp.page, page_size=pp.page_size
    )


def export_rows(db: Session, user: User, q: Select[tuple[AuditLog]]) -> list[list[str]]:
    rows = [
        [
            str(r.occurred_at),
            r.actor.full_name if r.actor else r.actor_type,
            r.action,
            r.entity_type or "",
            str(r.entity_id or ""),
            r.result,
            str(r.ip or ""),
            r.request_id or "",
        ]
        for r in db.scalars(q.limit(10_000)).unique()
    ]
    record(db, "audit.export", "audit", None, {"rows": [None, len(rows)]})
    emit("BULK_EXPORT", user_id=user.id, details={"kind": "audit", "rows": len(rows)})
    return [
        ["occurred_at", "actor", "action", "entity_type", "entity_id", "result", "ip", "request_id"],
        *rows,
    ]
