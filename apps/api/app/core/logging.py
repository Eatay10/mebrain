"""Yapısal JSON log (structlog). Hassas alanlar maskelenir (R-SEC-10, T16)."""

import logging
import re
import sys
from typing import Any

import structlog

from app.core import context

_SENSITIVE_KEYS = {
    "password",
    "token",
    "authorization",
    "cookie",
    "set-cookie",
    "csrf",
    "csrf_token",
    "x-csrf-token",
    "secret",
    "session",
    "cth_session",
    "api_token",
    "body",
    "description",
}
_TOKEN_RE = re.compile(r"cth_[0-9a-f]{8}_[A-Za-z0-9_\-]+")


def _mask(value: Any) -> Any:
    if isinstance(value, str):
        return _TOKEN_RE.sub("cth_********", value)
    if isinstance(value, dict):
        return {k: ("***" if k.lower() in _SENSITIVE_KEYS else _mask(v)) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [_mask(v) for v in value]
    return value


def _redact(_: Any, __: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    return {k: ("***" if k.lower() in _SENSITIVE_KEYS else _mask(v)) for k, v in event_dict.items()}


def _add_context(_: Any, __: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    ctx = context.current()
    event_dict.setdefault("request_id", ctx.request_id)
    if ctx.user_id:
        event_dict.setdefault("user_id", str(ctx.user_id))
    return event_dict


def configure_logging(service: str) -> None:
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=logging.INFO)
    for noisy in ("uvicorn.access",):
        logging.getLogger(noisy).disabled = True
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True, key="ts"),
            _add_context,
            _redact,
            structlog.processors.EventRenamer("msg"),
            structlog.processors.JSONRenderer(ensure_ascii=False),
        ],
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    structlog.contextvars.bind_contextvars(service=service)


log = structlog.get_logger()
