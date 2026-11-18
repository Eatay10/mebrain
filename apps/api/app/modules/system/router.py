import time
from collections import defaultdict
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app import contract as c
from app.auth.deps import SessionOnly
from app.auth.deps import current_user as _cu
from app.auth.policies import can_read_security, require
from app.core import metrics
from app.db import get_db
from app.models import JobRun, User

router = APIRouter(tags=["System"])
VERSION = "1.0.0"
JOBS = [
    "generate_recurring_tasks",
    "due_soon_notifications",
    "overdue_notifications",
    "send_email_notifications",
    "cleanup_sessions",
]
WINDOWS = {"15m": 900, "1h": 3600, "24h": 86400}


@router.get("/health", operation_id="getHealth", response_model=c.HealthStatus)
def health() -> c.HealthStatus:
    return c.HealthStatus(status="ok", version=VERSION)


@router.get(
    "/ready",
    operation_id="getReadiness",
    response_model=c.HealthStatus,
    responses={503: {"model": c.HealthStatus}},
)
def ready(db: Session = Depends(get_db)) -> c.HealthStatus | JSONResponse:
    try:
        db.execute(text("SELECT 1"))
        return c.HealthStatus(status="ok", checks={"database": "ok"}, version=VERSION)
    except Exception:
        body = c.HealthStatus(status="down", checks={"database": "down"}, version=VERSION)
        return JSONResponse(body.model_dump(by_alias=True), status_code=503)


@router.get(
    "/system/metrics-summary",
    operation_id="getMetricsSummary",
    response_model=c.MetricsSummary,
    dependencies=[SessionOnly],
)
def metrics_summary(
    window: Annotated[Literal["15m", "1h", "24h"], Query()] = "1h",
    user: User = Depends(_cu),
    db: Session = Depends(get_db),
) -> c.MetricsSummary:
    require(can_read_security(user), user, "metrics.read")
    groups: dict[tuple[str, str], list[metrics.Sample]] = defaultdict(list)
    for s in metrics.recent.since(WINDOWS[window]):
        if s.route.startswith("/api/v1/system"):
            continue
        groups[(s.route, s.method)].append(s)
    endpoints = []
    for (route, method), samples in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        durations = [x.duration_ms for x in samples]
        errors = sum(1 for x in samples if x.status >= 500)
        endpoints.append(
            c.Endpoint(
                route=route,
                method=method,
                requests=len(samples),
                error_rate=round(errors / len(samples), 4),
                p50_ms=metrics.percentile(durations, 50),
                p95_ms=metrics.percentile(durations, 95),
                p99_ms=metrics.percentile(durations, 99),
            )
        )
    latest = {}
    sub = select(JobRun.job, func.max(JobRun.started_at).label("m")).group_by(JobRun.job).subquery()
    for run in db.scalars(
        select(JobRun).join(sub, (JobRun.job == sub.c.job) & (JobRun.started_at == sub.c.m))
    ):
        latest[run.job] = run
    jobs = [
        c.Job(
            name=j,
            last_run_at=latest[j].started_at if j in latest else None,
            last_status=latest[j].status if j in latest else "NEVER_RAN",
            last_duration_ms=latest[j].duration_ms if j in latest else None,
        )
        for j in JOBS
    ]
    return c.MetricsSummary(
        window=window, uptime_seconds=int(time.time() - metrics.STARTED_AT), endpoints=endpoints, jobs=jobs
    )
