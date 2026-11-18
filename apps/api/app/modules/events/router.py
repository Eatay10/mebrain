from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app import contract as c
from app.auth.deps import current_user, require_scope
from app.core.schemas import PageParams, page_params
from app.db import get_db
from app.models import User
from app.modules.events import service

router = APIRouter(tags=["Events"])
READ = [Depends(require_scope("events:read"))]
WRITE = [Depends(require_scope("events:write"))]


@router.get("/events", operation_id="listEvents", response_model=c.EventPage, dependencies=READ)
def list_events(
    q: Annotated[str | None, Query(max_length=100)] = None,
    scope: Annotated[c.EventScope | None, Query()] = None,
    type: Annotated[c.EventType | None, Query()] = None,  # noqa: A002
    frm: Annotated[date | None, Query(alias="from")] = None,
    to: Annotated[date | None, Query()] = None,
    participant_id: Annotated[str | None, Query(alias="participantId", max_length=36)] = None,
    pp: PageParams = Depends(page_params),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> c.EventPage:
    return service.list_events(db, user, pp, q, scope, type, frm, to, participant_id)


@router.post(
    "/events", operation_id="createEvent", response_model=c.Event, status_code=201, dependencies=WRITE
)
def create_event(
    body: c.EventCreate, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> c.Event:
    return service.create(db, user, body)


@router.get("/events/{eventId}", operation_id="getEvent", response_model=c.Event, dependencies=READ)
def get_event(eventId: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)) -> c.Event:  # noqa: N803
    return service.get(db, user, eventId)


@router.patch("/events/{eventId}", operation_id="updateEvent", response_model=c.Event, dependencies=WRITE)
def update_event(
    eventId: UUID,
    body: c.EventUpdate,
    user: User = Depends(current_user),  # noqa: N803
    db: Session = Depends(get_db),
) -> c.Event:
    return service.update(db, user, eventId, body)


@router.delete("/events/{eventId}", operation_id="deleteEvent", status_code=204, dependencies=WRITE)
def delete_event(
    eventId: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> Response:  # noqa: N803
    service.delete(db, user, eventId)
    return Response(status_code=204)


@router.get(
    "/events/{eventId}/participations",
    operation_id="listEventParticipations",
    response_model=list[c.Participation],
    dependencies=READ,
)
def list_participations(
    eventId: UUID,
    user: User = Depends(current_user),  # noqa: N803
    db: Session = Depends(get_db),
) -> list[c.Participation]:
    return service.list_participations(db, user, eventId)


@router.post(
    "/events/{eventId}/participations",
    operation_id="requestParticipation",
    response_model=c.Participation,
    status_code=201,
    dependencies=WRITE,
)
def request_participation(
    eventId: UUID,
    body: c.ParticipationCreate,
    user: User = Depends(current_user),  # noqa: N803
    db: Session = Depends(get_db),
) -> c.Participation:
    return service.request(db, user, eventId, body)


@router.patch(
    "/participations/{participationId}",
    operation_id="decideParticipation",
    response_model=c.Participation,
    dependencies=WRITE,
)
def decide_participation(
    participationId: UUID,
    body: c.ParticipationDecision,  # noqa: N803
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> c.Participation:
    return service.decide(db, user, participationId, body)
