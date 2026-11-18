from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import contract as c
from app.auth.deps import SessionOnly, current_user
from app.core.schemas import PageParams, page_params
from app.db import get_db
from app.models import User
from app.modules.security import service

router = APIRouter(tags=["Security"], dependencies=[SessionOnly])


@router.get("/security/events", operation_id="listSecurityEvents", response_model=c.SecurityEventPage)
def list_security_events(
    type: Annotated[c.SecurityEventType | None, Query()] = None,  # noqa: A002
    severity: Annotated[c.SecuritySeverity | None, Query()] = None,
    frm: Annotated[datetime | None, Query(alias="from")] = None,
    to: Annotated[datetime | None, Query()] = None,
    pp: PageParams = Depends(page_params),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> c.SecurityEventPage:
    return service.list_events(
        db, user, pp, type.value if type else None, severity.value if severity else None, frm, to
    )


@router.get("/security/summary", operation_id="getSecuritySummary", response_model=c.SecuritySummary)
def security_summary(
    window: Annotated[Literal["1h", "24h", "7d"], Query()] = "24h",
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> c.SecuritySummary:
    return service.summary(db, user, window)
