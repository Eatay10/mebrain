"""Audit kaydı (R-PY-08). İstekle aynı transaction'da yazılır: işlem geri alınırsa kayıt da düşer."""

from datetime import date, datetime
from enum import Enum
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.core import context
from app.models import AuditLog

_SECRET_FIELDS = {"password", "password_hash", "token", "token_hash", "csrf_token"}


def _plain(v: Any) -> Any:
    if isinstance(v, Enum):
        return v.value
    if isinstance(v, UUID | date | datetime):
        return str(v)
    return v


def diff(before: dict[str, Any], after: dict[str, Any]) -> dict[str, list[Any]]:
    return {
        k: [_plain(before.get(k)), _plain(after.get(k))]
        for k in after
        if k not in _SECRET_FIELDS and before.get(k) != after.get(k)
    }


def record(
    db: Session,
    action: str,
    entity_type: str | None = None,
    entity_id: UUID | None = None,
    changes: dict[str, Any] | None = None,
    result: str = "SUCCESS",
    actor_id: UUID | None = None,
) -> None:
    ctx = context.current()
    clean = {k: v for k, v in (changes or {}).items() if k not in _SECRET_FIELDS} or None
    db.add(
        AuditLog(
            actor_id=actor_id or ctx.user_id,
            actor_type=ctx.actor_type,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            changes=clean,
            ip=ctx.ip,
            user_agent=ctx.user_agent,
            request_id=ctx.request_id,
            result=result,
        )
    )
