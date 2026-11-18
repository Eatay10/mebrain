"""RBAC kapsamı — knowledge/domain/rbac-scope.md.

Organizasyon: Direktör → Unit (UNIT_MANAGER) → Ekip (MANAGER) → Ekip üyesi (EMPLOYEE).

- Direktör ve denetmen tüm ekipleri görür.
- Unit yöneticisi kendi unit'indeki tüm ekipleri (yöneticileri ve üyeleriyle) görür ve yönetir.
- Yönetici kendi ekibini ve yönettiği ekipleri görür ve yönetir.
- Çalışan kendi ekibini görür.
- Herkes, ekibinden bağımsız olarak kişisel olarak dahil olduğu task'ları (sorumlu, yedek, çalışma arkadaşı,
  talep sahibi, oluşturan) görür.
"""

from uuid import UUID

from sqlalchemy import ColumnElement, and_, exists, false, or_, select, true
from sqlalchemy.orm import Session

from app.contract import Role
from app.models import Task, TaskCollaborator, Team, Unit, User

ALL = None  # "tüm ekipler" işareti
MANAGING_ROLES = (Role.MANAGER, Role.UNIT_MANAGER, Role.DIRECTOR)


def managed_unit_ids(db: Session, user: User) -> set[UUID] | None:
    if user.role == Role.DIRECTOR:
        return ALL
    if user.role == Role.UNIT_MANAGER:
        return set(db.scalars(select(Unit.id).where(Unit.manager_id == user.id)))
    return set()


def managed_team_ids(db: Session, user: User) -> set[UUID] | None:
    if user.role == Role.DIRECTOR:
        return ALL
    teams: set[UUID] = set()
    if user.role in (Role.MANAGER, Role.UNIT_MANAGER):
        teams |= set(db.scalars(select(Team.id).where(Team.manager_id == user.id)))
    if user.role == Role.UNIT_MANAGER:
        units = managed_unit_ids(db, user) or set()
        if units:
            teams |= set(db.scalars(select(Team.id).where(Team.unit_id.in_(units))))
    return teams


def visible_team_ids(db: Session, user: User) -> set[UUID] | None:
    if user.role in (Role.DIRECTOR, Role.AUDITOR):
        return ALL
    teams = {user.team_id} if user.team_id else set()
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


def involved_filter(user_id: UUID) -> ColumnElement[bool]:
    """Kullanıcının kişisel olarak dahil olduğu task'lar."""
    return or_(
        Task.assignee_id == user_id,
        Task.backup_assignee_id == user_id,
        Task.requester_id == user_id,
        Task.created_by == user_id,
        exists().where(TaskCollaborator.task_id == Task.id, TaskCollaborator.user_id == user_id),
    )


def is_involved(task: Task, user_id: UUID) -> bool:
    return user_id in (task.assignee_id, task.backup_assignee_id, task.requester_id, task.created_by) or any(
        c.id == user_id for c in task.collaborators
    )


def visible_task_filter(db: Session, user: User) -> ColumnElement[bool]:
    scope = visible_team_ids(db, user)
    if scope is ALL:
        return true()
    return or_(team_filter(Task.team_id, scope), involved_filter(user.id))


def assignable_filter(db: Session, user: User) -> ColumnElement[bool]:
    """Kullanıcının task atayabileceği kişiler (User sorgusu için).

    Direktör: aktif herkes (öncelikle unit yöneticileri). Unit yöneticisi: unit'indeki ekiplerin yöneticileri
    ve üyeleri. Yönetici: yönettiği ekiplerin üyeleri. Çalışan: yalnızca kendisi. Denetmen: kimse.
    """
    if user.role == Role.AUDITOR:
        return false()
    base = and_(User.is_active.is_(True), User.role != Role.AUDITOR)
    if user.role == Role.DIRECTOR:
        return base
    if user.role == Role.EMPLOYEE:
        return User.id == user.id
    teams = managed_team_ids(db, user) or set()
    team_managers = select(Team.manager_id).where(Team.id.in_(teams), Team.manager_id.is_not(None))
    return and_(base, or_(User.id == user.id, User.team_id.in_(teams), User.id.in_(team_managers)))


def can_assign_to(db: Session, user: User, target_id: UUID) -> bool:
    return db.scalar(select(User.id).where(User.id == target_id, assignable_filter(db, user))) is not None
