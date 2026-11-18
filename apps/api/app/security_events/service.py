"""Güvenlik olayları (knowledge OBSERVABILITY §5). İstek işlemi geri alınsa bile kalıcı olsun diye
kendi kısa oturumunda yazılır."""

from typing import Any
from uuid import UUID

from app.core import context, metrics
from app.core.logging import log

SEVERITY = {
    "LOGIN_SUCCESS": "INFO",
    "LOGIN_FAILED": "LOW",
    "ACCOUNT_LOCKED": "MEDIUM",
    "LOGOUT": "INFO",
    "SESSION_EXPIRED": "INFO",
    "CSRF_REJECTED": "MEDIUM",
    "AUTHZ_DENIED": "MEDIUM",
    "NOT_FOUND_PROBE": "LOW",
    "VALIDATION_REJECTED": "INFO",
    "PAYLOAD_TOO_LARGE": "LOW",
    "RATE_LIMITED": "LOW",
    "ROLE_CHANGED": "HIGH",
    "USER_DEACTIVATED": "MEDIUM",
    "API_TOKEN_CREATED": "INFO",
    "API_TOKEN_REVOKED": "INFO",
    "API_TOKEN_INVALID": "MEDIUM",
    "BULK_EXPORT": "MEDIUM",
}


def emit(
    event_type: str,
    *,
    user_id: UUID | None = None,
    severity: str | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    from app.db import SessionLocal
    from app.models import SecurityEvent

    ctx = context.current()
    sev = severity or SEVERITY.get(event_type, "INFO")
    metrics.SECURITY_EVENTS.labels(event_type, sev).inc()
    log.info("security_event", type=event_type, severity=sev)
    try:
        with SessionLocal() as db:
            db.add(
                SecurityEvent(
                    type=event_type,
                    severity=sev,
                    user_id=user_id or ctx.user_id,
                    ip=ctx.ip,
                    request_id=ctx.request_id,
                    details=details,
                )
            )
            db.commit()
    except Exception as exc:  # olay kaydı asla isteği düşürmemeli
        log.error("security_event_write_failed", error_type=type(exc).__name__)
