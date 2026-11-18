from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app import contract as c
from app.auth.deps import SessionOnly, current_user
from app.core.csv_export import csv_response
from app.core.schemas import PageParams, page_params
from app.db import get_db
from app.models import User
from app.modules.audit import service

router = APIRouter(tags=["Audit"], dependencies=[SessionOnly])


@router.get(
    "/audit-logs",
    operation_id="listAuditLogs",
    response_model=c.AuditLogPage,
    responses={200: {"content": {"text/csv": {}}}},
)
def list_audit_logs(
    actor_id: Annotated[UUID | None, Query(alias="actorId")] = None,
    action: Annotated[str | None, Query(max_length=60)] = None,
    entity_type: Annotated[str | None, Query(alias="entityType", max_length=40)] = None,
    entity_id: Annotated[UUID | None, Query(alias="entityId")] = None,
    frm: Annotated[datetime | None, Query(alias="from")] = None,
    to: Annotated[datetime | None, Query()] = None,
    format: Annotated[Literal["json", "csv"], Query()] = "json",  # noqa: A002
    pp: PageParams = Depends(page_params),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> c.AuditLogPage | Response:
    q = service.query(db, user, actor_id, action, entity_type, entity_id, frm, to)
    if format == "csv":
        return csv_response(service.export_rows(db, user, q), "audit-log.csv")
    return service.page(db, q, pp)
