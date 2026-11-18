"""İstek boru hattı: request ID, bağlam, boyut limiti, rate limit, güvenlik başlıkları, metrik, log."""

import hashlib
import ipaddress
import re
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response

from app.config import get_settings
from app.core import context, metrics
from app.core.errors import problem
from app.core.logging import log
from app.core.ratelimit import limiter

_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._-]{8,64}$")
SECURITY_HEADERS = {
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Cross-Origin-Opener-Policy": "same-origin",
}


def _client_ip(request: Request) -> str | None:
    host = request.client.host if request.client else None
    try:
        return str(ipaddress.ip_address(host)) if host else None
    except ValueError:
        return None


_UPLOAD_PATHS = re.compile(r"^/api/v1/(tasks|events)/[0-9a-fA-F-]{36}/(attachments|photos)$")


def _body_limit(request: Request) -> int:
    """Dosya yükleme uçlarında daha büyük gövdeye izin verilir (multipart ek yükü için +64 KB)."""
    s = get_settings()
    if request.method == "POST" and _UPLOAD_PATHS.match(request.url.path):
        return s.max_upload_bytes + 64 * 1024
    return s.max_body_bytes


def _rate_key(request: Request) -> tuple[str, int, str]:
    s = get_settings()
    ip = _client_ip(request) or "unknown"
    if request.url.path.endswith("/auth/login"):
        return f"login:{ip}", s.rate_limit_login_per_min, "login"
    cred = request.headers.get("authorization") or request.cookies.get("cth_session")
    if cred:
        digest = hashlib.sha256(cred.encode()).hexdigest()[:16]
        return f"auth:{digest}", s.rate_limit_authenticated_per_min, "authenticated"
    return f"anon:{ip}", s.rate_limit_anonymous_per_min, "anonymous"


def install_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def pipeline(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        from app.security_events.service import emit

        incoming = request.headers.get("x-request-id", "")
        request_id = incoming if _REQUEST_ID_RE.match(incoming) else uuid.uuid4().hex
        context.set_context(
            context.RequestContext(
                request_id=request_id,
                ip=_client_ip(request),
                user_agent=(request.headers.get("user-agent") or "")[:300] or None,
            )
        )
        started = time.perf_counter()
        is_api = request.url.path.startswith("/api/")

        response: Response
        length = request.headers.get("content-length")
        if length and length.isdigit() and int(length) > _body_limit(request):
            emit("PAYLOAD_TOO_LARGE", details={"route": request.url.path, "bytes": int(length)})
            response = problem(
                413, "Payload Too Large", "/problems/payload-too-large", instance=request.url.path
            )
        elif (
            is_api
            and not request.url.path.endswith(("/health", "/ready"))
            and (retry := limiter.hit(*_rate_key(request)[:2]))
        ):
            emit("RATE_LIMITED", details={"route": request.url.path, "bucket": _rate_key(request)[2]})
            response = problem(
                429,
                "Too Many Requests",
                "/problems/rate-limited",
                instance=request.url.path,
                headers={"Retry-After": str(retry)},
            )
        else:
            response = await call_next(request)

        duration_ms = (time.perf_counter() - started) * 1000
        route_obj = request.scope.get("route")
        route = getattr(route_obj, "path", None) or "unmatched"
        if is_api and route.startswith("/") and not route.startswith("/api/"):
            route = "/api/v1" + route  # alt router şablonu önek olmadan gelir
        response.headers["X-Request-ID"] = request_id
        for k, v in SECURITY_HEADERS.items():
            response.headers.setdefault(k, v)
        if is_api:
            response.headers["Cache-Control"] = "no-store"
            metrics.HTTP_REQUESTS.labels(request.method, route, str(response.status_code)).inc()
            metrics.HTTP_DURATION.labels(request.method, route).observe(duration_ms / 1000)
            metrics.recent.add(
                metrics.Sample(time.time(), request.method, route, response.status_code, duration_ms)
            )
        log.info(
            "request",
            method=request.method,
            route=route,
            status=response.status_code,
            duration_ms=round(duration_ms, 1),
        )
        return response
