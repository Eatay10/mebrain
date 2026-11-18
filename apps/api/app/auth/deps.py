"""Kimlik doğrulama bağımlılıkları: cookie oturumu (+CSRF) veya Bearer API token (+scope).

API token etkin yetkisi = token scope'ları ∩ kullanıcı rolü (ADR-0002). Scope eşlemesi olmayan uç
noktalar API token ile kullanılamaz (sadece web oturumu).
"""

import hashlib
import hmac
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import timedelta

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core import context
from app.core.errors import Forbidden, Unauthorized
from app.db import get_db
from app.models import ApiToken, User, UserSession
from app.models.base import utcnow
from app.security_events.service import emit

SESSION_COOKIE = "cth_session"
CSRF_COOKIE = "cth_csrf"
UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


@dataclass
class Principal:
    user: User
    auth_type: str  # "session" | "token"
    session: UserSession | None = None
    scopes: set[str] = field(default_factory=set)


def _from_token(db: Session, raw: str) -> Principal:
    token = db.scalar(select(ApiToken).where(ApiToken.token_hash == sha256(raw)))
    now = utcnow()
    if token is None or token.revoked_at is not None or token.expires_at <= now or not token.user.is_active:
        emit("API_TOKEN_INVALID", details={"reason": "unknown_revoked_or_expired"})
        raise Unauthorized("Geçersiz API token'ı.")
    if token.last_used_at is None or now - token.last_used_at > timedelta(minutes=1):
        token.last_used_at = now
    ctx = context.current()
    ctx.user_id, ctx.actor_type = token.user_id, "API_TOKEN"
    return Principal(user=token.user, auth_type="token", scopes=set(token.scopes))


def _from_session(db: Session, request: Request, raw: str) -> Principal:
    s = get_settings()
    sess = db.get(UserSession, sha256(raw))
    now = utcnow()
    if sess is None:
        raise Unauthorized("Oturum bulunamadı.")
    idle_limit = sess.last_seen_at + timedelta(minutes=s.session_idle_minutes)
    if sess.expires_at <= now or idle_limit <= now or not sess.user.is_active:
        db.delete(sess)
        db.commit()
        emit("SESSION_EXPIRED", user_id=sess.user_id)
        raise Unauthorized("Oturum süresi doldu.")
    ctx = context.current()
    ctx.user_id, ctx.actor_type = sess.user_id, "USER"
    if request.method in UNSAFE_METHODS:
        header = request.headers.get("x-csrf-token", "")
        if not header or not hmac.compare_digest(header, sess.csrf_token):
            emit("CSRF_REJECTED", user_id=sess.user_id, details={"route": request.url.path})
            raise Forbidden("CSRF doğrulaması başarısız.")
    if now - sess.last_seen_at > timedelta(seconds=30):
        sess.last_seen_at = now
    return Principal(user=sess.user, auth_type="session", session=sess)


def current_principal(request: Request, db: Session = Depends(get_db)) -> Principal:
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        return _from_token(db, auth[7:].strip())
    raw = request.cookies.get(SESSION_COOKIE)
    if raw:
        return _from_session(db, request, raw)
    raise Unauthorized("Kimlik doğrulaması gerekli.")


def require_scope(scope: str | None) -> Callable[[Principal], Principal]:
    """Uç noktanın API token ile kullanılabilmesi için gereken scope. None = sadece web oturumu."""

    def dep(principal: Principal = Depends(current_principal)) -> Principal:
        if principal.auth_type == "token" and (scope is None or scope not in principal.scopes):
            emit(
                "AUTHZ_DENIED",
                user_id=principal.user.id,
                details={"reason": "token_scope", "required": scope},
            )
            raise Forbidden("API token'ı bu işlem için yetkili değil.")
        return principal

    return dep


def current_user(principal: Principal = Depends(current_principal)) -> User:
    return principal.user


SessionOnly = Depends(require_scope(None))
