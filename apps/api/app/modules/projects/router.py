from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app import contract as c
from app.auth.deps import SessionOnly, current_user, require_scope
from app.core.schemas import PageParams, page_params
from app.db import get_db
from app.models import User
from app.modules.projects import service

router = APIRouter(tags=["Projects"])
READ = [Depends(require_scope("projects:read"))]


@router.get("/projects", operation_id="listProjects", response_model=c.ProjectPage, dependencies=READ)
def list_projects(
    q: Annotated[str | None, Query(max_length=100)] = None,
    team_id: Annotated[UUID | None, Query(alias="teamId")] = None,
    status: Annotated[c.ProjectStatus | None, Query()] = None,
    pp: PageParams = Depends(page_params),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> c.ProjectPage:
    return service.list_projects(db, user, pp, q, team_id, status)


@router.post(
    "/projects",
    operation_id="createProject",
    response_model=c.Project,
    status_code=201,
    dependencies=[SessionOnly],
)
def create_project(
    body: c.ProjectCreate, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> c.Project:
    return service.create(db, user, body)


@router.get("/projects/{projectId}", operation_id="getProject", response_model=c.Project, dependencies=READ)
def get_project(
    projectId: UUID,
    user: User = Depends(current_user),  # noqa: N803
    db: Session = Depends(get_db),
) -> c.Project:
    return service.get(db, user, projectId)


@router.patch(
    "/projects/{projectId}",
    operation_id="updateProject",
    response_model=c.Project,
    dependencies=[SessionOnly],
)
def update_project(
    projectId: UUID,
    body: c.ProjectUpdate,
    user: User = Depends(current_user),  # noqa: N803
    db: Session = Depends(get_db),
) -> c.Project:
    return service.update(db, user, projectId, body)


@router.delete(
    "/projects/{projectId}", operation_id="deleteProject", status_code=204, dependencies=[SessionOnly]
)
def delete_project(
    projectId: UUID,
    user: User = Depends(current_user),  # noqa: N803
    db: Session = Depends(get_db),
) -> Response:
    service.delete(db, user, projectId)
    return Response(status_code=204)
