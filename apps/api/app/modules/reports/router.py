from datetime import date
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app import contract as c
from app.auth.deps import SessionOnly, current_user, require_scope
from app.core.csv_export import csv_response
from app.db import get_db
from app.models import User
from app.modules.reports import schedules, service

router = APIRouter(tags=["Reports"])
GroupBy = Literal["team", "assignee", "project", "status", "priority", "category", "type"]


@router.get(
    "/reports/tasks",
    operation_id="getTaskReport",
    response_model=c.TaskReport,
    responses={200: {"content": {"text/csv": {}}}},
    dependencies=[Depends(require_scope("reports:read"))],
)
def task_report(
    group_by: Annotated[GroupBy, Query(alias="groupBy")],
    frm: Annotated[date, Query(alias="from")],
    to: Annotated[date, Query()],
    team_id: Annotated[UUID | None, Query(alias="teamId")] = None,
    project_id: Annotated[UUID | None, Query(alias="projectId")] = None,
    format: Annotated[Literal["json", "csv"], Query()] = "json",  # noqa: A002
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> c.TaskReport | Response:
    report = service.build(db, user, group_by, frm, to, team_id, project_id)
    if format == "csv":
        return csv_response(service.csv_rows(db, user, report), f"task-report-{group_by}-{frm}-{to}.csv")
    return report


@router.get(
    "/report-schedules",
    operation_id="listReportSchedules",
    response_model=list[c.ReportSchedule],
    dependencies=[SessionOnly],
)
def list_schedules(
    user: User = Depends(current_user), db: Session = Depends(get_db)
) -> list[c.ReportSchedule]:
    return schedules.list_mine(db, user)


@router.post(
    "/report-schedules",
    operation_id="createReportSchedule",
    response_model=c.ReportSchedule,
    status_code=201,
    dependencies=[SessionOnly],
)
def create_schedule(
    body: c.ReportScheduleCreate, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> c.ReportSchedule:
    return schedules.create(db, user, body)


@router.patch(
    "/report-schedules/{scheduleId}",
    operation_id="updateReportSchedule",
    response_model=c.ReportSchedule,
    dependencies=[SessionOnly],
)
def update_schedule(
    scheduleId: UUID,  # noqa: N803
    body: c.ReportScheduleUpdate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> c.ReportSchedule:
    return schedules.update(db, user, scheduleId, body)


@router.delete(
    "/report-schedules/{scheduleId}",
    operation_id="deleteReportSchedule",
    status_code=204,
    dependencies=[SessionOnly],
)
def delete_schedule(
    scheduleId: UUID,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),  # noqa: N803
) -> Response:
    schedules.delete(db, user, scheduleId)
    return Response(status_code=204)


@router.post(
    "/report-schedules/{scheduleId}/run",
    operation_id="runReportSchedule",
    status_code=202,
    dependencies=[SessionOnly],
)
def run_schedule(
    scheduleId: UUID,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),  # noqa: N803
) -> Response:
    schedules.run_now(db, user, scheduleId)
    return Response(status_code=202)
