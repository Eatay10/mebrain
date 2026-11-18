"""Yetki kararlarının TEK kaynağı (R-SEC-02). knowledge/domain/rbac-scope.md policy tablosu.

Her fonksiyon bool döner; servisler `require()` ile çağırır. Ret → 403 + AUTHZ_DENIED.
Kapsam dışı nesneler servislerde 404 olarak ele alınır (varlık sızdırmamak için).
"""

from uuid import UUID

from sqlalchemy.orm import Session

from app.auth.scope import in_scope, is_read_only, managed_team_ids, visible_team_ids
from app.contract import EventScope, ParticipationStatus, Role, TaskStatus, TaskType
from app.core.errors import Forbidden
from app.models import Event, EventParticipation, Project, Task, User
from app.security_events.service import emit


def require(allowed: bool, user: User, action: str, entity: str | None = None) -> None:
    if not allowed:
        emit("AUTHZ_DENIED", user_id=user.id, details={"action": action, "entity": entity})
        raise Forbidden("Bu işlem için yetkiniz yok.")


def _manages(db: Session, user: User, team_id: UUID | None) -> bool:
    return not is_read_only(user) and in_scope(team_id, managed_team_ids(db, user))


# ------------------------------------------------------------------ tasks
def can_read_task(db: Session, user: User, task: Task) -> bool:
    return in_scope(task.team_id, visible_team_ids(db, user))


def can_create_task(
    db: Session, user: User, team_id: UUID, task_type: TaskType, assignee_id: UUID | None
) -> bool:
    if is_read_only(user):
        return False
    if user.role == Role.EMPLOYEE:
        return task_type == TaskType.STANDARD and team_id == user.team_id and assignee_id in (None, user.id)
    return _manages(db, user, team_id)


def can_update_task(db: Session, user: User, task: Task) -> bool:
    return _manages(db, user, task.team_id)


def can_transition(db: Session, user: User, task: Task, to: TaskStatus) -> bool:
    if is_read_only(user):
        return False
    if _manages(db, user, task.team_id):
        return True
    if task.status == TaskStatus.DONE:  # yeniden açma sadece yönetici+
        return False
    return user.id in (task.assignee_id, task.backup_assignee_id)


def can_delete_task(db: Session, user: User, task: Task) -> bool:
    return _manages(db, user, task.team_id)


def can_comment(db: Session, user: User, task: Task) -> bool:
    return not is_read_only(user) and can_read_task(db, user, task)


# ------------------------------------------------------------------ projects
def can_read_project(db: Session, user: User, project: Project) -> bool:
    return in_scope(project.team_id, visible_team_ids(db, user))


def can_manage_project(db: Session, user: User, team_id: UUID) -> bool:
    return _manages(db, user, team_id)


# ------------------------------------------------------------------ users / teams
def can_read_user(db: Session, user: User, target: User) -> bool:
    if user.id == target.id or user.role in (Role.DIRECTOR, Role.AUDITOR):
        return True
    return in_scope(target.team_id, visible_team_ids(db, user))


def can_manage_users(user: User) -> bool:
    return user.role == Role.DIRECTOR


def can_change_role(user: User, target: User) -> bool:
    return user.role == Role.DIRECTOR and user.id != target.id


def is_manager_of(db: Session, user: User, target: User) -> bool:
    return target.team_id is not None and _manages(db, user, target.team_id)


# ------------------------------------------------------------------ events
def can_create_event(user: User, scope: EventScope) -> bool:
    if is_read_only(user):
        return False
    return scope == EventScope.INDIVIDUAL or user.role == Role.DIRECTOR


def can_edit_event(user: User, event: Event) -> bool:
    return not is_read_only(user) and (event.created_by == user.id or user.role == Role.DIRECTOR)


def can_request_participation(db: Session, user: User, target: User) -> bool:
    if is_read_only(user):
        return False
    return target.id == user.id or user.role == Role.DIRECTOR or is_manager_of(db, user, target)


def can_decide_participation(db: Session, user: User, p: EventParticipation, to: ParticipationStatus) -> bool:
    if is_read_only(user):
        return False
    if to == ParticipationStatus.CANCELLED and p.user_id == user.id:
        return True
    return user.role == Role.DIRECTOR or is_manager_of(db, user, p.user)


# ------------------------------------------------------------------ competencies
def can_manage_catalog(user: User) -> bool:
    return user.role in (Role.MANAGER, Role.DIRECTOR)


def can_verify_competency(db: Session, user: User, target: User) -> bool:
    return user.id != target.id and (user.role == Role.DIRECTOR or is_manager_of(db, user, target))


def can_read_team_matrix(db: Session, user: User, team_id: UUID) -> bool:
    return user.role in (Role.DIRECTOR, Role.AUDITOR) or _manages(db, user, team_id)


# ------------------------------------------------------------------ comms / audit / security
def can_announce(db: Session, user: User, scope: str, team_id: UUID | None) -> bool:
    if is_read_only(user):
        return False
    if scope == "ORGANIZATION":
        return user.role == Role.DIRECTOR
    return team_id is not None and _manages(db, user, team_id)


def can_read_audit(user: User) -> bool:
    return user.role in (Role.MANAGER, Role.DIRECTOR, Role.AUDITOR)


def can_read_security(user: User) -> bool:
    return user.role in (Role.DIRECTOR, Role.AUDITOR)
