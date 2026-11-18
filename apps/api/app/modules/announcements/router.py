from uuid import UUID

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app import contract as c
from app.auth.deps import SessionOnly, current_user
from app.core.schemas import PageParams, page_params
from app.db import get_db
from app.models import User
from app.modules.announcements import service

router = APIRouter(tags=["Announcements"], dependencies=[SessionOnly])


@router.get("/announcements", operation_id="listAnnouncements", response_model=c.AnnouncementPage)
def list_announcements(
    pp: PageParams = Depends(page_params), user: User = Depends(current_user), db: Session = Depends(get_db)
) -> c.AnnouncementPage:
    return service.list_for(db, user, pp)


@router.post(
    "/announcements", operation_id="createAnnouncement", response_model=c.Announcement, status_code=201
)
def create_announcement(
    body: c.AnnouncementCreate, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> c.Announcement:
    return service.create(db, user, body)


@router.delete("/announcements/{announcementId}", operation_id="deleteAnnouncement", status_code=204)
def delete_announcement(
    announcementId: UUID,
    user: User = Depends(current_user),  # noqa: N803
    db: Session = Depends(get_db),
) -> Response:
    service.delete(db, user, announcementId)
    return Response(status_code=204)
