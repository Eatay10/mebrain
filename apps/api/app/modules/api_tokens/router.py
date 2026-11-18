from uuid import UUID

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app import contract as c
from app.auth.deps import SessionOnly, current_user
from app.db import get_db
from app.models import User
from app.modules.api_tokens import service

router = APIRouter(tags=["Me"], dependencies=[SessionOnly])


@router.get("/me/api-tokens", operation_id="listMyApiTokens", response_model=list[c.ApiToken])
def list_tokens(user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[c.ApiToken]:
    return service.list_mine(db, user)


@router.post(
    "/me/api-tokens", operation_id="createMyApiToken", response_model=c.ApiTokenCreated, status_code=201
)
def create_token(
    body: c.ApiTokenCreate, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> c.ApiTokenCreated:
    return service.create(db, user, body)


@router.delete("/me/api-tokens/{tokenId}", operation_id="revokeMyApiToken", status_code=204)
def revoke_token(
    tokenId: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> Response:  # noqa: N803
    service.revoke(db, user, tokenId)
    return Response(status_code=204)
