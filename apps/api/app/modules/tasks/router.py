from datetime import date
from typing import Annotated, Literal
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, Response, UploadFile
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
    watching: Annotated[bool | None, Query()] = None,
    has_backup: Annotated[bool | None, Query(alias="hasBackup")] = None,
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
        watching_user=user.id if watching else None,
        has_backup=has_backup,
    )
    return service.list_tasks(db, user, f, pp)


@router.get(
    "/tasks/assignee-suggestions",
    operation_id="suggestAssignees",
    response_model=list[c.AssigneeSuggestion],
    dependencies=READ,
)
def suggest_assignees(
    category: Annotated[c.TaskCategory, Query()],
    team_id: Annotated[UUID | None, Query(alias="teamId")] = None,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> list[c.AssigneeSuggestion]:
    return service.suggest_assignees(db, user, category, team_id)


@router.get(
    "/me/assignable-users",
    operation_id="listAssignableUsers",
    response_model=list[c.AssignableUser],
    tags=["Me"],
    dependencies=READ,
)
def assignable_users(
    team_id: Annotated[UUID | None, Query(alias="teamId")] = None,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> list[c.AssignableUser]:
    return service.assignable_users(db, user, team_id)


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
    service.delete_task(db, user, taskId)
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


@router.get(
    "/tasks/{taskId}/progress",
    operation_id="listTaskProgress",
    response_model=list[c.ProgressEntry],
    dependencies=READ,
)
def list_progress(
    taskId: UUID,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),  # noqa: N803
) -> list[c.ProgressEntry]:
    return service.list_progress(db, user, taskId)


@router.post(
    "/tasks/{taskId}/progress", operation_id="updateTaskProgress", response_model=c.Task, dependencies=WRITE
)
def update_progress(
    taskId: UUID,
    body: c.TaskProgressUpdate,
    user: User = Depends(current_user),  # noqa: N803
    db: Session = Depends(get_db),
) -> c.Task:
    return service.update_progress(db, user, taskId, body)


@router.put("/tasks/{taskId}/watch", operation_id="watchTask", status_code=204, dependencies=WRITE)
def watch(taskId: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)) -> Response:  # noqa: N803
    service.watch(db, user, taskId, True)
    return Response(status_code=204)


@router.delete("/tasks/{taskId}/watch", operation_id="unwatchTask", status_code=204, dependencies=WRITE)
def unwatch(taskId: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)) -> Response:  # noqa: N803
    service.watch(db, user, taskId, False)
    return Response(status_code=204)


@router.get(
    "/tasks/{taskId}/watchers",
    operation_id="listTaskWatchers",
    response_model=list[c.UserRef],
    dependencies=READ,
)
def watchers(
    taskId: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> list[c.UserRef]:  # noqa: N803
    return service.list_watchers(db, user, taskId)


@router.get(
    "/tasks/{taskId}/attachments",
    operation_id="listTaskAttachments",
    response_model=list[c.Attachment],
    dependencies=READ,
)
def list_attachments(
    taskId: UUID,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),  # noqa: N803
) -> list[c.Attachment]:
    return service.list_attachments(db, user, taskId)


@router.post(
    "/tasks/{taskId}/attachments",
    operation_id="uploadTaskAttachment",
    response_model=c.Attachment,
    status_code=201,
    dependencies=WRITE,
)
async def upload_attachment(
    taskId: UUID,  # noqa: N803
    file: UploadFile = File(...),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> c.Attachment:
    data = await read_limited(file)
    return service.add_attachment(db, user, taskId, file.filename, file.content_type, data)


@router.get("/attachments/{attachmentId}", operation_id="downloadAttachment", dependencies=READ)
def download_attachment(
    attachmentId: UUID,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),  # noqa: N803
) -> Response:
    a = service.download_attachment(db, user, attachmentId)
    return Response(
        content=a.data,
        media_type=a.content_type,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(a.file_name)}",
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "private, no-store",
        },
    )


@router.delete(
    "/attachments/{attachmentId}", operation_id="deleteAttachment", status_code=204, dependencies=WRITE
)
def delete_attachment(
    attachmentId: UUID,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),  # noqa: N803
) -> Response:
    service.delete_attachment(db, user, attachmentId)
    return Response(status_code=204)


async def read_limited(file: UploadFile) -> bytes:
    """Dosyayı en fazla limit+1 bayt okur (Content-Length'e güvenmeden)."""
    from app.config import get_settings

    return await file.read(get_settings().max_upload_bytes + 1)
