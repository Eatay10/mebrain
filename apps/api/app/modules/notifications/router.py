from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app import contract as c
from app.auth.deps import SessionOnly, current_user
from app.core.schemas import PageParams, page_params
from app.db import get_db
from app.models import User
from app.modules.notifications import service

router = APIRouter(tags=["Notifications"], dependencies=[SessionOnly])


@router.get("/notifications", operation_id="listNotifications", response_model=c.NotificationPage)
def list_notifications(
    unread: Annotated[bool | None, Query()] = None,
    pp: PageParams = Depends(page_params),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> c.NotificationPage:
    return service.list_for(db, user, pp, unread)


@router.get("/notifications/unread-count", operation_id="getUnreadNotificationCount")
def unread_count(user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict[str, int]:
    return {"count": service.unread_count(db, user)}


@router.post("/notifications/{notificationId}/read", operation_id="markNotificationRead", status_code=204)
def mark_read(
    notificationId: UUID,
    user: User = Depends(current_user),  # noqa: N803
    db: Session = Depends(get_db),
) -> Response:
    service.mark_read(db, user, notificationId)
    return Response(status_code=204)


@router.post("/notifications/read-all", operation_id="markAllNotificationsRead", status_code=204)
def mark_all(user: User = Depends(current_user), db: Session = Depends(get_db)) -> Response:
    service.mark_all_read(db, user)
    return Response(status_code=204)
