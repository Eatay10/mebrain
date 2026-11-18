"""RBAC kapsamı — knowledge/domain/rbac-scope.md algoritmasının birebir uygulaması."""

from uuid import UUID

from sqlalchemy import ColumnElement, false, select, true
from sqlalchemy.orm import Session

from app.contract import Role
from app.models import Task, Team, User

ALL = None  # "tüm ekipler" işareti


def managed_team_ids(db: Session, user: User) -> set[UUID] | None:
    if user.role == Role.DIRECTOR:
        return ALL
    if user.role == Role.MANAGER:
        return set(db.scalars(select(Team.id).where(Team.manager_id == user.id)))
    return set()


def visible_team_ids(db: Session, user: User) -> set[UUID] | None:
    if user.role in (Role.DIRECTOR, Role.AUDITOR):
        return ALL
    teams = {user.team_id} if user.team_id else set()
    if user.role == Role.MANAGER:
        teams |= managed_team_ids(db, user) or set()
    return teams


def is_read_only(user: User) -> bool:
    return user.role == Role.AUDITOR


def in_scope(team_id: UUID | None, scope: set[UUID] | None) -> bool:
    return scope is ALL or (team_id is not None and team_id in scope)


def team_filter(column: ColumnElement, scope: set[UUID] | None) -> ColumnElement[bool]:
    if scope is ALL:
        return true()
    return column.in_(scope) if scope else false()


def visible_task_filter(db: Session, user: User) -> ColumnElement[bool]:
    return team_filter(Task.team_id, visible_team_ids(db, user))
