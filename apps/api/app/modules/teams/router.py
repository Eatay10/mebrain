from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import contract as c
from app.auth.deps import SessionOnly, current_user
from app.db import get_db
from app.models import User
from app.modules.teams import service

router = APIRouter(tags=["Teams"], dependencies=[SessionOnly])


@router.get("/teams", operation_id="listTeams", response_model=list[c.Team])
def list_teams(user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[c.Team]:
    return service.list_teams(db, user)


@router.post("/teams", operation_id="createTeam", response_model=c.Team, status_code=201)
def create_team(
    body: c.TeamCreate, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> c.Team:
    return service.create(db, user, body)


@router.get("/teams/{teamId}", operation_id="getTeam", response_model=c.Team)
def get_team(teamId: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)) -> c.Team:  # noqa: N803
    return service.get(db, user, teamId)


@router.patch("/teams/{teamId}", operation_id="updateTeam", response_model=c.Team)
def update_team(
    teamId: UUID,
    body: c.TeamUpdate,
    user: User = Depends(current_user),  # noqa: N803
    db: Session = Depends(get_db),
) -> c.Team:
    return service.update(db, user, teamId, body)
