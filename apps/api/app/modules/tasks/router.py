from datetime import date
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app import contract as c
from app.auth.deps import current_user, require_scope
from app.core.errors import BadRequest
from app.core.schemas import PageParams, page_params
from app.db import get_db
from app.models import User
from app.modules.tasks import service
from app.modules.tasks.repository import TaskFilters

router = APIRouter(tags=["Tasks"])
READ = [Depends(require_scope("tasks:read"))]
WRITE = [Depends(require_scope("tasks:write"))]
Sort = Literal[
    "dueDate", "-dueDate", "priority", "-priority", "createdAt", "-createdAt", "updatedAt", "-updatedAt"
]


def _csv_enum[E](raw: str | None, enum: type[E], field: str) -> list[E] | None:
    if not raw:
        return None
    try:
        return [enum(v.strip()) for v in raw.split(",") if v.strip()]  # type: ignore[call-arg]
    except ValueError as exc:
        raise BadRequest(errors=[{"field": field, "message": "Geçersiz değer."}]) from exc


def _assignee(raw: str | None, user: User) -> UUID | None:
    if not raw:
        return None
    if raw == "me":
        return user.id
    try:
        return UUID(raw)
    except ValueError as exc:
        raise BadRequest(errors=[{"field": "assigneeId", "message": "UUID veya 'me' olmalı."}]) from exc


@router.get("/tasks", operation_id="listTasks", response_model=c.TaskPage, dependencies=READ)
def list_tasks(
    q: Annotated[str | None, Query(max_length=100)] = None,
    type: Annotated[c.TaskType | None, Query()] = None,  # noqa: A002
    status: Annotated[str | None, Query()] = None,
    priority: Annotated[str | None, Query()] = None,
    category: Annotated[c.TaskCategory | None, Query()] = None,
    team_id: Annotated[UUID | None, Query(alias="teamId")] = None,
    project_id: Annotated[UUID | None, Query(alias="projectId")] = None,
    assignee_id: Annotated[str | None, Query(alias="assigneeId", max_length=36)] = None,
    overdue: Annotated[bool | None, Query()] = None,
    recurring: Annotated[bool | None, Query()] = None,
    due_from: Annotated[date | None, Query(alias="dueFrom")] = None,
    due_to: Annotated[date | None, Query(alias="dueTo")] = None,
    sort: Annotated[Sort, Query()] = "-updatedAt",
    pp: PageParams = Depends(page_params),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> c.TaskPage:
    f = TaskFilters(
        q=q,
        type=type,
        status=_csv_enum(status, c.TaskStatus, "status"),
        priority=_csv_enum(priority, c.TaskPriority, "priority"),
        category=category,
        team_id=team_id,
        project_id=project_id,
        assignee_id=_assignee(assignee_id, user),
        overdue=overdue,
        recurring=recurring,
        due_from=due_from,
        due_to=due_to,
        sort=sort,
    )
    return service.list_tasks(db, user, f, pp)


@router.post("/tasks", operation_id="createTask", response_model=c.Task, status_code=201, dependencies=WRITE)
def create_task(
    body: c.TaskCreate, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> c.Task:
    return service.create(db, user, body)


@router.get("/tasks/{taskId}", operation_id="getTask", response_model=c.Task, dependencies=READ)
def get_task(taskId: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)) -> c.Task:  # noqa: N803
    return service.get(db, user, taskId)


@router.patch("/tasks/{taskId}", operation_id="updateTask", response_model=c.Task, dependencies=WRITE)
def update_task(
    taskId: UUID,
    body: c.TaskUpdate,
    user: User = Depends(current_user),  # noqa: N803
    db: Session = Depends(get_db),
) -> c.Task:
    return service.update(db, user, taskId, body)


@router.delete("/tasks/{taskId}", operation_id="deleteTask", status_code=204, dependencies=WRITE)
def delete_task(taskId: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)) -> Response:  # noqa: N803
    service.delete(db, user, taskId)
    return Response(status_code=204)


@router.post(
    "/tasks/{taskId}/transitions", operation_id="transitionTask", response_model=c.Task, dependencies=WRITE
)
def transition_task(
    taskId: UUID,
    body: c.TaskTransition,
    user: User = Depends(current_user),  # noqa: N803
    db: Session = Depends(get_db),
) -> c.Task:
    return service.transition(db, user, taskId, body)


@router.get(
    "/tasks/{taskId}/comments",
    operation_id="listTaskComments",
    response_model=c.CommentPage,
    dependencies=READ,
)
def list_comments(
    taskId: UUID,
    pp: PageParams = Depends(page_params),
    user: User = Depends(current_user),  # noqa: N803
    db: Session = Depends(get_db),
) -> c.CommentPage:
    return service.list_comments(db, user, taskId, pp)


@router.post(
    "/tasks/{taskId}/comments",
    operation_id="addTaskComment",
    response_model=c.Comment,
    status_code=201,
    dependencies=WRITE,
)
def add_comment(
    taskId: UUID,
    body: c.CommentCreate,
    user: User = Depends(current_user),  # noqa: N803
    db: Session = Depends(get_db),
) -> c.Comment:
    return service.add_comment(db, user, taskId, body)


@router.get(
    "/tasks/{taskId}/history",
    operation_id="getTaskHistory",
    response_model=list[c.AuditLogEntry],
    dependencies=READ,
)
def task_history(
    taskId: UUID,
    user: User = Depends(current_user),  # noqa: N803
    db: Session = Depends(get_db),
) -> list[c.AuditLogEntry]:
    return service.history(db, user, taskId)
