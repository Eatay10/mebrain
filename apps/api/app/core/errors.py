"""RFC 9457 problem+json hataları (R-SEC-06). İç ayrıntı istemciye dönmez."""

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core import context
from app.core.logging import log

PROBLEM_JSON = "application/problem+json"


class ApiError(Exception):
    status = 500
    title = "Internal Server Error"
    type_ = "about:blank"

    def __init__(
        self, detail: str | None = None, errors: list[dict[str, str]] | None = None, **kw: Any
    ) -> None:
        super().__init__(detail or self.title)
        self.detail = detail
        self.errors = errors
        self.headers: dict[str, str] = kw.get("headers", {})


class BadRequest(ApiError):
    status, title, type_ = 400, "Bad Request", "/problems/validation"


class Unauthorized(ApiError):
    status, title, type_ = 401, "Unauthorized", "/problems/unauthorized"


class Forbidden(ApiError):
    status, title, type_ = 403, "Forbidden", "/problems/forbidden"


class NotFound(ApiError):
    status, title, type_ = 404, "Not Found", "/problems/not-found"


class Conflict(ApiError):
    status, title, type_ = 409, "Conflict", "/problems/conflict"


class PayloadTooLarge(ApiError):
    status, title, type_ = 413, "Payload Too Large", "/problems/payload-too-large"


class InvalidTransition(ApiError):
    status, title, type_ = 422, "Invalid Transition", "/problems/invalid-transition"


class Locked(ApiError):
    status, title, type_ = 423, "Locked", "/problems/locked"


class TooManyRequests(ApiError):
    status, title, type_ = 429, "Too Many Requests", "/problems/rate-limited"


def problem(
    status: int,
    title: str,
    type_: str = "about:blank",
    detail: str | None = None,
    errors: list[dict[str, str]] | None = None,
    instance: str | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    body: dict[str, Any] = {
        "type": type_,
        "title": title,
        "status": status,
        "requestId": context.current().request_id,
    }
    if detail:
        body["detail"] = detail
    if errors:
        body["errors"] = errors
    if instance:
        body["instance"] = instance
    return JSONResponse(body, status_code=status, media_type=PROBLEM_JSON, headers=headers)


def _validation_errors(exc: RequestValidationError) -> list[dict[str, str]]:
    out = []
    for err in exc.errors():
        loc = [str(p) for p in err.get("loc", []) if p not in ("body", "query", "path", "header")]
        # Değerin kendisi asla yansıtılmaz (hassas veri sızıntısı önlemi).
        out.append({"field": ".".join(loc) or "request", "message": str(err.get("msg", "invalid"))})
    return out


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api_error(request: Request, exc: ApiError) -> JSONResponse:
        return problem(
            exc.status, exc.title, exc.type_, exc.detail, exc.errors, request.url.path, exc.headers or None
        )

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        from app.security_events.service import emit

        errors = _validation_errors(exc)
        emit(
            "VALIDATION_REJECTED",
            details={"fields": [e["field"] for e in errors][:10], "route": request.url.path},
        )
        return problem(
            400, "Bad Request", "/problems/validation", "İstek doğrulanamadı.", errors, request.url.path
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        titles = {404: "Not Found", 405: "Method Not Allowed"}
        return problem(exc.status_code, titles.get(exc.status_code, "Error"), instance=request.url.path)

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        log.error("unhandled_error", error_type=type(exc).__name__, route=request.url.path)
        return problem(500, "Internal Server Error", instance=request.url.path)
