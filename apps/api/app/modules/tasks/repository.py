"""Task sorguları — her liste sorgusu kapsam filtresini uygular (R-SEC-03)."""

from dataclasses import dataclass
from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.orm import Session

from app.auth.policies import can_read_task
from app.auth.scope import visible_task_filter
from app.contract import Recurrence, TaskCategory, TaskPriority, TaskStatus, TaskType
from app.core.errors import NotFound
from app.models import Task, TaskCollaborator, TaskComment, TaskWatcher, User
from app.security_events.service import emit

PRIORITY_ORDER = {TaskPriority.LOW: 1, TaskPriority.MEDIUM: 2, TaskPriority.HIGH: 3, TaskPriority.CRITICAL: 4}


def escape_like(q: str) -> str:
    return q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def get_visible(db: Session, user: User, task_id: UUID) -> Task:
    task = db.get(Task, task_id)
    if task is None or task.deleted_at is not None:
        raise NotFound("Task bulunamadı.")
    if not can_read_task(db, user, task):
        emit("NOT_FOUND_PROBE", user_id=user.id, details={"entity": "task"})
        raise NotFound("Task bulunamadı.")
    return task


@dataclass
class TaskFilters:
    q: str | None = None
    type: TaskType | None = None
    status: list[TaskStatus] | None = None
    priority: list[TaskPriority] | None = None
    category: TaskCategory | None = None
    team_id: UUID | None = None
    project_id: UUID | None = None
    assignee_id: UUID | None = None
    overdue: bool | None = None
    recurring: bool | None = None
    due_from: date | None = None
    due_to: date | None = None
    sort: str = "-updatedAt"
    watching_user: UUID | None = None


def _sort_clause(sort: str) -> list[Any]:
    desc = sort.startswith("-")
    key = sort.lstrip("-")
    if key == "priority":
        from sqlalchemy import case

        col: Any = case({p.value: v for p, v in PRIORITY_ORDER.items()}, value=Task.priority)
    else:
        col = {"dueDate": Task.due_date, "createdAt": Task.created_at, "updatedAt": Task.updated_at}[key]
    primary = col.desc().nulls_last() if desc else col.asc().nulls_last()
    return [primary, Task.id]


def build_query(db: Session, user: User, f: TaskFilters) -> Select[tuple[Task]]:
    conds = [Task.deleted_at.is_(None), visible_task_filter(db, user)]
    conds.append(Task.recurrence != Recurrence.NONE if f.recurring else Task.recurrence == Recurrence.NONE)
    if f.q:
        pat = f"%{escape_like(f.q)}%"
        conds.append(or_(Task.title.ilike(pat, escape="\\"), Task.description.ilike(pat, escape="\\")))
    if f.type:
        conds.append(Task.type == f.type)
    if f.status:
        conds.append(Task.status.in_(f.status))
    if f.priority:
        conds.append(Task.priority.in_(f.priority))
    if f.category:
        conds.append(Task.category == f.category)
    if f.team_id:
        conds.append(Task.team_id == f.team_id)
    if f.project_id:
        conds.append(Task.project_id == f.project_id)
    if f.assignee_id:
        conds.append(
            or_(
                Task.assignee_id == f.assignee_id,
                Task.backup_assignee_id == f.assignee_id,
                Task.id.in_(
                    select(TaskCollaborator.task_id).where(TaskCollaborator.user_id == f.assignee_id)
                ),
            )
        )
    if f.watching_user:
        conds.append(Task.id.in_(select(TaskWatcher.task_id).where(TaskWatcher.user_id == f.watching_user)))
    if f.overdue is True:
        conds.append(and_(Task.status != TaskStatus.DONE, Task.due_date < date.today()))
    elif f.overdue is False:
        conds.append(
            or_(Task.status == TaskStatus.DONE, Task.due_date.is_(None), Task.due_date >= date.today())
        )
    if f.due_from:
        conds.append(Task.due_date >= f.due_from)
    if f.due_to:
        conds.append(Task.due_date <= f.due_to)
    return select(Task).where(*conds).order_by(*_sort_clause(f.sort))


def count(db: Session, q: Select[tuple[Task]]) -> int:
    return db.scalar(select(func.count()).select_from(q.order_by(None).subquery())) or 0


def comment_counts(db: Session, task_ids: list[UUID]) -> dict[UUID, int]:
    if not task_ids:
        return {}
    rows = db.execute(
        select(TaskComment.task_id, func.count())
        .where(TaskComment.task_id.in_(task_ids), TaskComment.deleted_at.is_(None))
        .group_by(TaskComment.task_id)
    )
    return {tid: n for tid, n in rows}
