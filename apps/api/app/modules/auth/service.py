"""Giriş / çıkış / oturum bilgisi (ADR-0002, T01–T03, T12)."""

import secrets
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import contract as c
from app.audit.service import record
from app.auth.deps import Principal, sha256
from app.auth.passwords import verify_password
from app.auth.scope import managed_team_ids, visible_team_ids
from app.config import get_settings
from app.core import context, metrics
from app.core.errors import Locked, Unauthorized
from app.core.schemas import to_user
from app.models import Team, User, UserSession
from app.models.base import utcnow
from app.security_events.service import emit

GENERIC_LOGIN_ERROR = "E-posta veya parola hatalı."


def _team_ids(db: Session, scope: set | None) -> list:
    return list(db.scalars(select(Team.id))) if scope is None else sorted(scope, key=str)


def session_payload(db: Session, user: User, csrf: str, expires_at=None) -> c.Session:
    return c.Session(
        user=to_user(user),
        csrf_token=csrf,
        visible_team_ids=_team_ids(db, visible_team_ids(db, user)),
        managed_team_ids=_team_ids(db, managed_team_ids(db, user)),
        expires_at=expires_at,
    )


def login(db: Session, email: str, password: str, old_session_raw: str | None) -> tuple[str, UserSession]:
    s = get_settings()
    now = utcnow()
    user = db.scalar(select(User).where(User.email == email))
    if user and user.locked_until and user.locked_until > now:
        verify_password(None, password)  # sabit süre
        metrics.AUTH_LOGINS.labels("locked").inc()
        emit("LOGIN_FAILED", user_id=user.id, details={"reason": "locked"})
        raise Locked("Hesap geçici olarak kilitli. Daha sonra tekrar deneyin.")

    ok = verify_password(user.password_hash if user else None, password)
    if not user or not ok or not user.is_active:
        metrics.AUTH_LOGINS.labels("failed").inc()
        emit(
            "LOGIN_FAILED",
            user_id=user.id if user else None,
            details={"reason": "bad_credentials" if not user or not ok else "inactive"},
        )
        if user and not ok:
            user.failed_login_count += 1
            if user.failed_login_count >= s.login_max_failures:
                user.locked_until = now + timedelta(minutes=s.login_lock_minutes)
                user.failed_login_count = 0
                emit("ACCOUNT_LOCKED", user_id=user.id)
            db.commit()
        raise Unauthorized(GENERIC_LOGIN_ERROR)

    if old_session_raw:  # session fixation koruması: eski oturum iptal
        old = db.get(UserSession, sha256(old_session_raw))
        if old:
            db.delete(old)
    user.failed_login_count = 0
    user.locked_until = None
    user.last_login_at = now
    raw = secrets.token_urlsafe(32)
    ctx = context.current()
    ctx.user_id = user.id
    sess = UserSession(
        id_hash=sha256(raw),
        user_id=user.id,
        csrf_token=secrets.token_urlsafe(32),
        ip=ctx.ip,
        user_agent=ctx.user_agent,
        last_seen_at=now,
        expires_at=now + timedelta(hours=s.session_hours),
    )
    db.add(sess)
    record(db, "auth.login", "user", user.id)
    metrics.AUTH_LOGINS.labels("success").inc()
    emit("LOGIN_SUCCESS", user_id=user.id)
    sess.user = user
    return raw, sess


def logout(db: Session, principal: Principal) -> None:
    if principal.session is not None:
        db.delete(principal.session)
    record(db, "auth.logout", "user", principal.user.id)
    emit("LOGOUT", user_id=principal.user.id)
