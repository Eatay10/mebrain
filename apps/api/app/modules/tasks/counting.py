"""Durum sayımları — knowledge/domain/dashboard-counting.md.

Değişmezler: todo + in_progress + blocked + done = total; overdue ⊆ açık task'lar.
Tekrarlayan şablonlar (recurrence != NONE) ve silinmiş task'lar sayılmaz.
"""

from collections.abc import Sequence
from datetime import date
from typing import Any

from sqlalchemy import ColumnElement, and_, func, select
from sqlalchemy.orm import Session

from app import contract as c
from app.contract import Recurrence, TaskStatus
from app.models import Task


def live_task_filter() -> ColumnElement[bool]:
    return and_(Task.deleted_at.is_(None), Task.recurrence == Recurrence.NONE)


def _count_columns(today: date) -> list[Any]:
    return [
        func.count().filter(Task.status == TaskStatus.TODO).label("todo"),
        func.count().filter(Task.status == TaskStatus.IN_PROGRESS).label("in_progress"),
        func.count().filter(Task.status == TaskStatus.BLOCKED).label("blocked"),
        func.count().filter(Task.status == TaskStatus.DONE).label("done"),
        func.count().filter(and_(Task.status != TaskStatus.DONE, Task.due_date < today)).label("overdue"),
        func.count().label("total"),
    ]


def empty() -> c.StatusCounts:
    return c.StatusCounts(todo=0, in_progress=0, blocked=0, done=0, overdue=0, total=0)


def _row_counts(row: Any) -> c.StatusCounts:
    return c.StatusCounts(
        todo=row.todo,
        in_progress=row.in_progress,
        blocked=row.blocked,
        done=row.done,
        overdue=row.overdue,
        total=row.total,
    )


def counts(db: Session, where: Sequence[ColumnElement[bool]]) -> c.StatusCounts:
    row = db.execute(select(*_count_columns(date.today())).where(live_task_filter(), *where)).one()
    return _row_counts(row)


def counts_by(
    db: Session, keys: Sequence[Any], where: Sequence[ColumnElement[bool]]
) -> dict[tuple[Any, ...], c.StatusCounts]:
    stmt = select(*keys, *_count_columns(date.today())).where(live_task_filter(), *where).group_by(*keys)
    return {tuple(row[: len(keys)]): _row_counts(row) for row in db.execute(stmt)}


def add(a: c.StatusCounts, b: c.StatusCounts) -> c.StatusCounts:
    return c.StatusCounts(
        todo=a.todo + b.todo,
        in_progress=a.in_progress + b.in_progress,
        blocked=a.blocked + b.blocked,
        done=a.done + b.done,
        overdue=a.overdue + b.overdue,
        total=a.total + b.total,
    )
