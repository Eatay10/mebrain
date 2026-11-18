from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import contract as c
from app.auth.deps import SessionOnly, current_user
from app.core.schemas import PageParams, page_params, to_user
from app.db import get_db
from app.models import User
from app.modules.users import service

router = APIRouter(tags=["Users"], dependencies=[SessionOnly])


@router.get("/users", operation_id="listUsers", response_model=c.UserPage)
def list_users(
    q: Annotated[str | None, Query(max_length=100)] = None,
    team_id: Annotated[UUID | None, Query(alias="teamId")] = None,
    role: Annotated[c.Role | None, Query()] = None,
    is_active: Annotated[bool | None, Query(alias="isActive")] = None,
    pp: PageParams = Depends(page_params),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> c.UserPage:
    return service.list_users(db, user, pp, q, team_id, role, is_active)


@router.post("/users", operation_id="createUser", response_model=c.User, status_code=201)
def create_user(
    body: c.UserCreate, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> c.User:
    return service.create(db, user, body)


@router.get("/users/{userId}", operation_id="getUser", response_model=c.User)
def get_user(userId: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)) -> c.User:  # noqa: N803
    return to_user(service.get_visible(db, user, userId))


@router.patch("/users/{userId}", operation_id="updateUser", response_model=c.User)
def update_user(
    userId: UUID,
    body: c.UserUpdate,
    user: User = Depends(current_user),  # noqa: N803
    db: Session = Depends(get_db),
) -> c.User:
    return service.update(db, user, userId, body)
