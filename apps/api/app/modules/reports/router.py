from datetime import date
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app import contract as c
from app.auth.deps import current_user, require_scope
from app.core.csv_export import csv_response
from app.db import get_db
from app.models import User
from app.modules.reports import service

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
