"""İstek bağlamı (request id, istemci IP, kullanıcı) — log, audit ve güvenlik olayları için."""

from contextvars import ContextVar
from dataclasses import dataclass
from uuid import UUID


@dataclass
class RequestContext:
    request_id: str = "-"
    ip: str | None = None
    user_agent: str | None = None
    user_id: UUID | None = None
    actor_type: str = "USER"  # USER | API_TOKEN | SYSTEM


_ctx: ContextVar[RequestContext | None] = ContextVar("request_context", default=None)


def current() -> RequestContext:
    ctx = _ctx.get()
    if ctx is None:
        ctx = RequestContext(actor_type="SYSTEM")
        _ctx.set(ctx)
    return ctx


def set_context(ctx: RequestContext) -> None:
    _ctx.set(ctx)
