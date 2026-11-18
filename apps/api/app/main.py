"""Cyber Task Hub API giriş noktası."""

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.config import get_settings
from app.core.errors import install_error_handlers
from app.core.logging import configure_logging
from app.core.middleware import install_middleware
from app.modules.announcements.router import router as announcements
from app.modules.api_tokens.router import router as api_tokens
from app.modules.audit.router import router as audit
from app.modules.auth.router import router as auth
from app.modules.competencies.router import router as competencies
from app.modules.dashboard.router import router as dashboard
from app.modules.events.router import router as events
from app.modules.notifications.router import router as notifications
from app.modules.projects.router import router as projects
from app.modules.reports.router import router as reports
from app.modules.security.router import router as security
from app.modules.system.router import router as system
from app.modules.tasks.router import router as tasks
from app.modules.teams.router import router as teams
from app.modules.users.router import router as users

API_PREFIX = "/api/v1"


def create_app() -> FastAPI:
    configure_logging("api")
    settings = get_settings()
    app = FastAPI(
        title="Cyber Task Hub API",
        version="1.0.0",
        openapi_url=f"{API_PREFIX}/openapi.json",
        docs_url=f"{API_PREFIX}/docs" if settings.env != "production" else None,
        redoc_url=None,
    )
    install_error_handlers(app)
    install_middleware(app)
    if settings.cors_origin_list:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origin_list,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
            allow_headers=["Content-Type", "X-CSRF-Token", "X-Request-ID", "Authorization"],
            expose_headers=["X-Request-ID", "Retry-After"],
        )
    api = APIRouter(prefix=API_PREFIX)
    for r in (
        system,
        auth,
        api_tokens,
        users,
        teams,
        projects,
        tasks,
        dashboard,
        reports,
        notifications,
        announcements,
        events,
        competencies,
        audit,
        security,
    ):
        api.include_router(r)
    app.include_router(api)

    @app.get("/metrics", include_in_schema=False)
    def prometheus_metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return app


app = create_app()
