from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import contract as c
from app.auth.deps import current_user, require_scope
from app.db import get_db
from app.models import User
from app.modules.dashboard import service

router = APIRouter(tags=["Dashboard"])


@router.get(
    "/dashboard/summary",
    operation_id="getDashboardSummary",
    response_model=c.DashboardSummary,
    dependencies=[Depends(require_scope("reports:read"))],
)
def dashboard_summary(
    team_id: Annotated[UUID | None, Query(alias="teamId")] = None,
    frm: Annotated[date | None, Query(alias="from")] = None,
    to: Annotated[date | None, Query()] = None,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> c.DashboardSummary:
    return service.summary(db, user, team_id, frm, to)
