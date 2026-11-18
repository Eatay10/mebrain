"""Task iş kuralları — knowledge/domain/task-lifecycle.md ve rbac-scope.md."""

from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import contract as c
from app.audit.service import diff, record
from app.auth import policies as P
from app.auth.scope import in_scope, visible_team_ids
from app.contract import NotificationType as NT
from app.contract import Recurrence, Role, TaskStatus, TaskType
from app.core import metrics
from app.core.errors import BadRequest, Conflict, InvalidTransition, NotFound
from app.core.schemas import PageParams, user_ref
from app.models import AuditLog, Project, Task, TaskComment, Team, User
from app.models.base import utcnow
from app.modules.notifications.service import notify
from app.modules.tasks import repository as repo

A, M = "A", "M"  # A = assignee/backup/yönetici+, M = sadece yönetici+
ALLOWED: dict[tuple[TaskStatus, TaskStatus], str] = {
    (TaskStatus.TODO, TaskStatus.IN_PROGRESS): A,
    (TaskStatus.TODO, TaskStatus.BLOCKED): A,
    (TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED): A,
    (TaskStatus.IN_PROGRESS, TaskStatus.DONE): A,
    (TaskStatus.BLOCKED, TaskStatus.TODO): A,
    (TaskStatus.BLOCKED, TaskStatus.IN_PROGRESS): A,
    (TaskStatus.DONE, TaskStatus.IN_PROGRESS): M,
}
STATUS_TR = {
    TaskStatus.TODO: "Başlanmadı",
    TaskStatus.IN_PROGRESS: "Devam ediyor",
    TaskStatus.BLOCKED: "Bloklu",
    TaskStatus.DONE: "Tamamlandı",
}
TRACKED = (
    "title",
    "description",
    "priority",
    "category",
    "assignee_id",
    "backup_assignee_id",
    "due_date",
    "recurrence",
    "status",
    "blocked_reason",
)


def _snapshot(t: Task) -> dict[str, Any]:
    return {k: getattr(t, k) for k in TRACKED}


def to_contract(t: Task, comment_count: int | None = None) -> c.Task:
    return c.Task(
        id=t.id,
        type=t.type,
        team_id=t.team_id,
        team_name=t.team.name if t.team else None,
        project=c.Project1(id=t.project.id, name=t.project.name) if t.project else None,
        title=t.title,
        description=t.description,
        status=t.status,
        blocked_reason=t.blocked_reason,
        priority=t.priority,
        category=t.category,
        assignee=user_ref(t.assignee),
        backup_assignee=user_ref(t.backup_assignee),
        due_date=t.due_date,
        is_overdue=bool(t.due_date and t.status != TaskStatus.DONE and t.due_date < date.today()),
        recurrence=t.recurrence,
        recurrence_parent_id=t.recurrence_parent_id,
        started_at=t.started_at,
        completed_at=t.completed_at,
        created_by=user_ref(t.creator),
        comment_count=comment_count,
        version=t.version,
        created_at=t.created_at,
        updated_at=t.updated_at,
    )


def get(db: Session, user: User, task_id: UUID) -> c.Task:
    t = repo.get_visible(db, user, task_id)
    return to_contract(t, repo.comment_counts(db, [t.id]).get(t.id, 0))


def list_tasks(db: Session, user: User, f: repo.TaskFilters, pp: PageParams) -> c.TaskPage:
    q = repo.build_query(db, user, f)
    total = repo.count(db, q)
    tasks = list(db.scalars(q.offset(pp.offset).limit(pp.page_size)).unique())
    cc = repo.comment_counts(db, [t.id for t in tasks])
    return c.TaskPage(
        items=[to_contract(t, cc.get(t.id, 0)) for t in tasks],
        total=total,
        page=pp.page,
        page_size=pp.page_size,
    )


def _check_member(db: Session, team_id: UUID, user_id: UUID | None, field: str) -> None:
    if user_id is None:
        return
    u = db.get(User, user_id)
    if u is None or not u.is_active or u.team_id != team_id:
        raise BadRequest(errors=[{"field": field, "message": "Kullanıcı bu ekibin aktif üyesi değil."}])


def _check_assignees(db: Session, team_id: UUID, assignee: UUID | None, backup: UUID | None) -> None:
    if backup is not None and backup == assignee:
        raise BadRequest(errors=[{"field": "backupAssigneeId", "message": "Yedek, sorumluyla aynı olamaz."}])
    _check_member(db, team_id, assignee, "assigneeId")
    _check_member(db, team_id, backup, "backupAssigneeId")


def _notify_assignment(
    db: Session, t: Task, actor: User, assignee_changed: bool, backup_changed: bool
) -> None:
    if assignee_changed and t.assignee_id:
        notify(
            db,
            [t.assignee_id],
            NT.TASK_ASSIGNED,
            f"Size task atandı: {t.title}",
            entity_type="task",
            entity_id=t.id,
            actor_id=actor.id,
        )
    if backup_changed and t.backup_assignee_id:
        notify(
            db,
            [t.backup_assignee_id],
            NT.TASK_BACKUP_ASSIGNED,
            f"Yedek sorumlu oldunuz: {t.title}",
            entity_type="task",
            entity_id=t.id,
            actor_id=actor.id,
        )


def create(db: Session, user: User, body: c.TaskCreate) -> c.Task:
    project: Project | None = None
    if body.type == TaskType.PROJECT:
        if body.project_id is None:
            raise BadRequest(errors=[{"field": "projectId", "message": "Proje task'ı için zorunlu."}])
        project = db.get(Project, body.project_id)
        if project is None or project.deleted_at is not None or not P.can_read_project(db, user, project):
            raise NotFound("Proje bulunamadı.")
        if body.team_id is not None and body.team_id != project.team_id:
            raise BadRequest(errors=[{"field": "teamId", "message": "Projenin ekibiyle uyuşmuyor."}])
        team_id = project.team_id
    else:
        if body.project_id is not None:
            raise BadRequest(errors=[{"field": "projectId", "message": "Standart task projeye bağlanamaz."}])
        team_id = body.team_id or (user.team_id if user.role == Role.EMPLOYEE else None)
        if team_id is None:
            raise BadRequest(errors=[{"field": "teamId", "message": "Standart task için zorunlu."}])
        if db.get(Team, team_id) is None or not in_scope(team_id, visible_team_ids(db, user)):
            raise NotFound("Ekip bulunamadı.")
    P.require(P.can_create_task(db, user, team_id, body.type, body.assignee_id), user, "task.create")
    _check_assignees(db, team_id, body.assignee_id, body.backup_assignee_id)
    t = Task(
        type=body.type,
        project_id=project.id if project else None,
        team_id=team_id,
        title=body.title,
        description=body.description,
        priority=body.priority or c.TaskPriority.MEDIUM,
        category=body.category or c.TaskCategory.OTHER,
        assignee_id=body.assignee_id,
        backup_assignee_id=body.backup_assignee_id,
        due_date=body.due_date,
        recurrence=body.recurrence or Recurrence.NONE,
        created_by=user.id,
    )
    db.add(t)
    db.flush()
    record(db, "task.create", "task", t.id, diff({}, _snapshot(t)))
    _notify_assignment(db, t, user, True, True)
    db.refresh(t)
    return to_contract(t, 0)


def update(db: Session, user: User, task_id: UUID, body: c.TaskUpdate) -> c.Task:
    t = repo.get_visible(db, user, task_id)
    P.require(P.can_update_task(db, user, t), user, "task.update", str(t.id))
    if t.version != body.version:
        raise Conflict("Task başka biri tarafından güncellendi. Sayfayı yenileyin.")
    fields = body.model_fields_set - {"version"}
    before = _snapshot(t)
    for name in fields:
        value = getattr(body, name)
        if name in ("title", "priority", "category", "recurrence") and value is None:
            raise BadRequest(errors=[{"field": name, "message": "Boş olamaz."}])
        setattr(t, name, value)
    _check_assignees(db, t.team_id, t.assignee_id, t.backup_assignee_id)
    changes = diff(before, _snapshot(t))
    if changes:
        t.version += 1
        record(db, "task.update", "task", t.id, changes)
        _notify_assignment(db, t, user, "assignee_id" in changes, "backup_assignee_id" in changes)
    db.flush()
    db.refresh(t)
    return to_contract(t, repo.comment_counts(db, [t.id]).get(t.id, 0))


def delete(db: Session, user: User, task_id: UUID) -> None:
    t = repo.get_visible(db, user, task_id)
    P.require(P.can_delete_task(db, user, t), user, "task.delete", str(t.id))
    t.deleted_at = utcnow()
    record(db, "task.delete", "task", t.id)


def transition(db: Session, user: User, task_id: UUID, body: c.TaskTransition) -> c.Task:
    t = repo.get_visible(db, user, task_id)
    if t.version != body.version:
        raise Conflict("Task başka biri tarafından güncellendi. Sayfayı yenileyin.")
    frm, to = t.status, body.to
    if (frm, to) not in ALLOWED:
        raise InvalidTransition(f"{frm.value} → {to.value} geçişi geçersiz.")
    P.require(P.can_transition(db, user, t, to), user, "task.transition", str(t.id))
    reason = (body.reason or "").strip()
    if to == TaskStatus.BLOCKED and not reason:
        raise BadRequest(errors=[{"field": "reason", "message": "Bloklu durumu için gerekçe zorunlu."}])
    now = utcnow()
    t.status = to
    if to == TaskStatus.IN_PROGRESS and t.started_at is None:
        t.started_at = now
    if to == TaskStatus.DONE:
        t.completed_at = now
    if frm == TaskStatus.DONE:
        t.completed_at = None
    t.blocked_reason = reason if to == TaskStatus.BLOCKED else None
    t.version += 1
    record(db, "task.transition", "task", t.id, {"status": [frm.value, to.value]})
    metrics.TASK_TRANSITIONS.labels(frm.value, to.value).inc()
    manager_id = t.team.manager_id if t.team else None
    notify(
        db,
        [t.created_by, manager_id, t.assignee_id],
        NT.TASK_STATUS_CHANGED,
        f"{t.title}: {STATUS_TR[to]}",
        body=reason or None,
        entity_type="task",
        entity_id=t.id,
        actor_id=user.id,
    )
    db.flush()
    db.refresh(t)
    return to_contract(t, repo.comment_counts(db, [t.id]).get(t.id, 0))


def _comment(cm: TaskComment) -> c.Comment:
    return c.Comment(
        id=cm.id, task_id=cm.task_id, author=user_ref(cm.author), body=cm.body, created_at=cm.created_at
    )


def list_comments(db: Session, user: User, task_id: UUID, pp: PageParams) -> c.CommentPage:
    t = repo.get_visible(db, user, task_id)
    base = select(TaskComment).where(TaskComment.task_id == t.id, TaskComment.deleted_at.is_(None))
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    rows = db.scalars(base.order_by(TaskComment.created_at).offset(pp.offset).limit(pp.page_size))
    return c.CommentPage(items=[_comment(x) for x in rows], total=total, page=pp.page, page_size=pp.page_size)


def add_comment(db: Session, user: User, task_id: UUID, body: c.CommentCreate) -> c.Comment:
    t = repo.get_visible(db, user, task_id)
    P.require(P.can_comment(db, user, t), user, "comment.create", str(t.id))
    text = body.body.strip()
    if not text:
        raise BadRequest(errors=[{"field": "body", "message": "Yorum boş olamaz."}])
    cm = TaskComment(task_id=t.id, author_id=user.id, body=text)
    db.add(cm)
    db.flush()
    record(db, "comment.create", "task", t.id, {"commentId": [None, str(cm.id)]})
    notify(
        db,
        [t.assignee_id, t.backup_assignee_id, t.created_by],
        NT.TASK_COMMENTED,
        f"{user.full_name} yorum yaptı: {t.title}",
        entity_type="task",
        entity_id=t.id,
        actor_id=user.id,
    )
    db.refresh(cm)
    return _comment(cm)


def history(db: Session, user: User, task_id: UUID) -> list[c.AuditLogEntry]:
    from app.modules.audit.service import to_contract as audit_entry

    t = repo.get_visible(db, user, task_id)
    rows = db.scalars(
        select(AuditLog)
        .where(AuditLog.entity_type == "task", AuditLog.entity_id == t.id)
        .order_by(AuditLog.occurred_at, AuditLog.id)
    )
    return [audit_entry(r) for r in rows]
