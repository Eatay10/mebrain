"""Kişisel API token'ları (ADR-0002, T09): düz metin bir kez döner, DB'de SHA-256 hash."""

import secrets
from datetime import timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import contract as c
from app.audit.service import record
from app.auth.deps import sha256
from app.config import get_settings
from app.core.errors import NotFound
from app.models import ApiToken, User
from app.models.base import utcnow
from app.security_events.service import emit


def _to_contract(t: ApiToken) -> c.ApiToken:
    return c.ApiToken(
        id=t.id,
        name=t.name,
        prefix=t.prefix,
        scopes=t.scopes,
        created_at=t.created_at,
        expires_at=t.expires_at,
        last_used_at=t.last_used_at,
        revoked_at=t.revoked_at,
    )


def list_mine(db: Session, user: User) -> list[c.ApiToken]:
    rows = db.scalars(
        select(ApiToken).where(ApiToken.user_id == user.id).order_by(ApiToken.created_at.desc())
    )
    return [_to_contract(t) for t in rows.unique()]


def create(db: Session, user: User, body: c.ApiTokenCreate) -> c.ApiTokenCreated:
    days = min(body.expires_in_days or 30, get_settings().api_token_max_days)
    prefix = secrets.token_hex(4)
    raw = f"cth_{prefix}_{secrets.token_urlsafe(32)}"
    t = ApiToken(
        user_id=user.id,
        name=body.name.strip(),
        prefix=prefix,
        token_hash=sha256(raw),
        scopes=sorted({s.value for s in body.scopes}),
        expires_at=utcnow() + timedelta(days=days),
    )
    db.add(t)
    db.flush()
    record(db, "api_token.create", "api_token", t.id, {"scopes": [None, t.scopes]})
    emit("API_TOKEN_CREATED", details={"tokenId": str(t.id), "scopes": t.scopes})
    db.refresh(t)
    return c.ApiTokenCreated(**_to_contract(t).model_dump(), token=raw)


def revoke(db: Session, user: User, token_id: UUID) -> None:
    t = db.get(ApiToken, token_id)
    if t is None or t.user_id != user.id:
        raise NotFound("Token bulunamadı.")
    if t.revoked_at is None:
        t.revoked_at = utcnow()
        record(db, "api_token.revoke", "api_token", t.id)
        emit("API_TOKEN_REVOKED", details={"tokenId": str(t.id)})
