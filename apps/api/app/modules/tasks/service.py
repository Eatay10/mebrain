"""Task iş kuralları — knowledge/domain/task-lifecycle.md ve rbac-scope.md.

Kişiler: talep sahibi (requester), ana sorumlu (assignee), yedek sorumlu (backup), çalışma arkadaşları
(collaborators). Takipçiler (watchers) yıldız koyan kişilerdir; yedek sorumlu otomatik takipçidir.
Task üzerindeki her güncelleme takipçilere bildirilir.
"""

import hashlib
from collections.abc import Iterable
from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import delete, func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app import contract as c
from app.audit.service import diff, record
from app.auth import policies as P
from app.auth.scope import assignable_filter, can_assign_to, in_scope, visible_team_ids
from app.config import get_settings
from app.contract import NotificationType as NT
from app.contract import Recurrence, Role, TaskStatus, TaskType
from app.core import metrics
from app.core.errors import BadRequest, Conflict, InvalidTransition, NotFound
from app.core.schemas import PageParams, user_ref
from app.models import (
    Attachment,
    AuditLog,
    Project,
    Task,
    TaskCollaborator,
    TaskComment,
    TaskProgressEntry,
    TaskWatcher,
    Team,
    User,
)
from app.models.base import utcnow
from app.modules.notifications.service import notify
from app.modules.tasks import repository as repo

A, M = "A", "M"  # A = sorumlu/yedek/çalışma arkadaşı/yönetici+, M = sadece yönetici+
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
FIELD_TR = {
    "title": "başlık",
    "description": "açıklama",
    "priority": "öncelik",
    "category": "kategori",
    "assignee_id": "sorumlu",
    "backup_assignee_id": "yedek sorumlu",
    "requester_id": "talep sahibi",
    "collaborators": "çalışma arkadaşları",
    "due_date": "son tarih",
    "recurrence": "tekrar",
}
TRACKED = (
    "title",
    "description",
    "priority",
    "category",
    "assignee_id",
    "backup_assignee_id",
    "requester_id",
    "due_date",
    "recurrence",
    "status",
    "blocked_reason",
    "progress",
)
ALLOWED_MIME_PREFIXES = ("image/", "text/", "application/pdf", "application/zip", "application/json")
ALLOWED_MIME_EXACT = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/msword",
    "application/vnd.ms-excel",
    "application/octet-stream",
}


def _snapshot(t: Task) -> dict[str, Any]:
    snap = {k: getattr(t, k) for k in TRACKED}
    snap["collaborators"] = sorted(str(u.id) for u in t.collaborators)
    return snap


# ------------------------------------------------------------------ okuma
class _Extras:
    """Liste/ayrıntı için kullanıcıya özgü sayaçlar (N+1 olmadan)."""

    def __init__(self, db: Session, user: User, ids: list[UUID]) -> None:
        self.comments = repo.comment_counts(db, ids)
        self.watchers: dict[UUID, int] = {}
        self.attachments: dict[UUID, int] = {}
        self.mine: set[UUID] = set()
        if not ids:
            return
        self.watchers = dict(
            db.execute(  # type: ignore[arg-type]
                select(TaskWatcher.task_id, func.count())
                .where(TaskWatcher.task_id.in_(ids))
                .group_by(TaskWatcher.task_id)
            ).all()
        )
        self.attachments = dict(
            db.execute(  # type: ignore[arg-type]
                select(Attachment.task_id, func.count())
                .where(Attachment.task_id.in_(ids), Attachment.deleted_at.is_(None))
                .group_by(Attachment.task_id)
            ).all()
        )
        self.mine = set(
            db.scalars(
                select(TaskWatcher.task_id).where(
                    TaskWatcher.task_id.in_(ids), TaskWatcher.user_id == user.id
                )
            )
        )


def to_contract(t: Task, ex: _Extras | None = None) -> c.Task:
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
        progress=t.progress,
        requester=user_ref(t.requester),
        assignee=user_ref(t.assignee),
        backup_assignee=user_ref(t.backup_assignee),
        collaborators=[user_ref(u) for u in t.collaborators],  # type: ignore[misc]
        is_watching=bool(ex and t.id in ex.mine),
        watcher_count=ex.watchers.get(t.id, 0) if ex else 0,
        attachment_count=ex.attachments.get(t.id, 0) if ex else 0,
        due_date=t.due_date,
        is_overdue=bool(t.due_date and t.status != TaskStatus.DONE and t.due_date < date.today()),
        recurrence=t.recurrence,
        recurrence_parent_id=t.recurrence_parent_id,
        started_at=t.started_at,
        completed_at=t.completed_at,
        created_by=user_ref(t.creator),
        comment_count=ex.comments.get(t.id, 0) if ex else None,
        version=t.version,
        created_at=t.created_at,
        updated_at=t.updated_at,
    )


def _one(db: Session, user: User, t: Task) -> c.Task:
    return to_contract(t, _Extras(db, user, [t.id]))


def get(db: Session, user: User, task_id: UUID) -> c.Task:
    return _one(db, user, repo.get_visible(db, user, task_id))


def list_tasks(db: Session, user: User, f: repo.TaskFilters, pp: PageParams) -> c.TaskPage:
    q = repo.build_query(db, user, f)
    total = repo.count(db, q)
    tasks = list(db.scalars(q.offset(pp.offset).limit(pp.page_size)).unique())
    ex = _Extras(db, user, [t.id for t in tasks])
    return c.TaskPage(
        items=[to_contract(t, ex) for t in tasks], total=total, page=pp.page, page_size=pp.page_size
    )


# ------------------------------------------------------------------ kişiler ve takipçiler
def watcher_ids(db: Session, task_id: UUID) -> set[UUID]:
    return set(db.scalars(select(TaskWatcher.user_id).where(TaskWatcher.task_id == task_id)))


def _add_watchers(db: Session, task_id: UUID, user_ids: Iterable[UUID | None]) -> None:
    rows = [{"task_id": task_id, "user_id": u, "created_at": utcnow()} for u in {x for x in user_ids if x}]
    if rows:
        db.execute(insert(TaskWatcher).values(rows).on_conflict_do_nothing())


def _audience(db: Session, t: Task, *extra: UUID | None) -> list[UUID | None]:
    """Bildirim alıcıları: verilen kişiler + tüm takipçiler (aktör notify() içinde elenir)."""
    return [*extra, *watcher_ids(db, t.id)]


def _active_user(db: Session, user_id: UUID, field: str) -> User:
    u = db.get(User, user_id)
    if u is None or not u.is_active:
        raise BadRequest(errors=[{"field": field, "message": "Aktif bir kullanıcı seçilmeli."}])
    return u


def _check_people(
    db: Session,
    actor: User,
    team_id: UUID,
    assignee: UUID | None,
    backup: UUID | None,
    collaborators: list[UUID],
    requester: UUID | None,
    changed: set[str] | None = None,
) -> None:
    """Atama kuralları: Direktör → unit yöneticileri (ve herkes), unit yöneticisi → unit'indeki yöneticiler ve
    ekipler, yönetici → ekip üyeleri, çalışan → kendisi (çalışma arkadaşı olarak ekip arkadaşları)."""

    def check(name: str) -> bool:
        return changed is None or name in changed

    if backup is not None and backup == assignee:
        raise BadRequest(errors=[{"field": "backupAssigneeId", "message": "Yedek, sorumluyla aynı olamaz."}])
    if check("assignee_id") and assignee is not None and not can_assign_to(db, actor, assignee):
        raise BadRequest(errors=[{"field": "assigneeId", "message": "Bu kişiye task atama yetkiniz yok."}])
    if check("backup_assignee_id") and backup is not None and not can_assign_to(db, actor, backup):
        raise BadRequest(
            errors=[{"field": "backupAssigneeId", "message": "Bu kişiyi yedek atama yetkiniz yok."}]
        )
    if check("collaborators"):
        for uid in collaborators:
            if uid in (assignee, backup):
                raise BadRequest(
                    errors=[
                        {
                            "field": "collaboratorIds",
                            "message": "Sorumlu/yedek ayrıca çalışma arkadaşı olamaz.",
                        }
                    ]
                )
            if actor.role == Role.EMPLOYEE:
                u = _active_user(db, uid, "collaboratorIds")
                ok = u.team_id == actor.team_id
            else:
                ok = can_assign_to(db, actor, uid)
            if not ok:
                raise BadRequest(
                    errors=[{"field": "collaboratorIds", "message": "Bu kişiyi ekleme yetkiniz yok."}]
                )
    if check("requester_id") and requester is not None:
        _active_user(db, requester, "requesterId")
    _ = team_id


def _set_collaborators(db: Session, t: Task, ids: list[UUID]) -> None:
    db.execute(delete(TaskCollaborator).where(TaskCollaborator.task_id == t.id))
    if ids:
        db.execute(
            insert(TaskCollaborator).values(
                [{"task_id": t.id, "user_id": u, "created_at": utcnow()} for u in ids]
            )
        )
    db.flush()
    db.expire(t, ["collaborators"])


def _notify_assignment(
    db: Session, t: Task, actor: User, assignee_changed: bool, backup_changed: bool, new_collabs: set[UUID]
) -> None:
    if assignee_changed and t.assignee_id:
        notify(
            db,
            [t.assignee_id],
            NT.TASK_ASSIGNED,
            f"Size task atandı: {t.title}",
            body=f"Atayan: {actor.full_name}",
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
            body="Bu task'ı otomatik olarak takip ediyorsunuz.",
            entity_type="task",
            entity_id=t.id,
            actor_id=actor.id,
        )
    if new_collabs:
        notify(
            db,
            new_collabs,
            NT.TASK_ASSIGNED,
            f"Çalışma arkadaşı olarak eklendiniz: {t.title}",
            body=f"Ekleyen: {actor.full_name}",
            entity_type="task",
            entity_id=t.id,
            actor_id=actor.id,
        )


# ------------------------------------------------------------------ yazma
def _resolve_team(db: Session, user: User, body: c.TaskCreate) -> tuple[UUID, Project | None]:
    if body.type == TaskType.PROJECT:
        if body.project_id is None:
            raise BadRequest(errors=[{"field": "projectId", "message": "Proje task'ı için zorunlu."}])
        project = db.get(Project, body.project_id)
        if project is None or project.deleted_at is not None or not P.can_read_project(db, user, project):
            raise NotFound("Proje bulunamadı.")
        if body.team_id is not None and body.team_id != project.team_id:
            raise BadRequest(errors=[{"field": "teamId", "message": "Projenin ekibiyle uyuşmuyor."}])
        return project.team_id, project
    if body.project_id is not None:
        raise BadRequest(errors=[{"field": "projectId", "message": "Standart task projeye bağlanamaz."}])
    team_id = body.team_id or (user.team_id if user.role == Role.EMPLOYEE else None)
    if team_id is None and body.assignee_id is not None:
        assignee = db.get(User, body.assignee_id)  # direktör → unit yöneticisi: sorumlunun ekibi
        team_id = assignee.team_id if assignee else None
    if team_id is None:
        raise BadRequest(errors=[{"field": "teamId", "message": "Standart task için zorunlu."}])
    if db.get(Team, team_id) is None or not in_scope(team_id, visible_team_ids(db, user)):
        raise NotFound("Ekip bulunamadı.")
    return team_id, None


def create(db: Session, user: User, body: c.TaskCreate) -> c.Task:
    team_id, project = _resolve_team(db, user, body)
    P.require(P.can_create_task(db, user, team_id, body.type, body.assignee_id), user, "task.create")
    collabs = list(dict.fromkeys(body.collaborator_ids or []))
    requester = body.requester_id or user.id
    _check_people(db, user, team_id, body.assignee_id, body.backup_assignee_id, collabs, requester)
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
        requester_id=requester,
        due_date=body.due_date,
        recurrence=body.recurrence or Recurrence.NONE,
        created_by=user.id,
    )
    db.add(t)
    db.flush()
    _set_collaborators(db, t, collabs)
    _add_watchers(db, t.id, [t.backup_assignee_id])
    record(db, "task.create", "task", t.id, diff({}, _snapshot(t)))
    _notify_assignment(db, t, user, True, True, set(collabs))
    db.refresh(t)
    return _one(db, user, t)


def _change_summary(changes: dict[str, Any]) -> str:
    names = [FIELD_TR[k] for k in changes if k in FIELD_TR]
    return ", ".join(names) if names else "ayrıntılar"


def update(db: Session, user: User, task_id: UUID, body: c.TaskUpdate) -> c.Task:
    t = repo.get_visible(db, user, task_id)
    P.require(P.can_update_task(db, user, t), user, "task.update", str(t.id))
    if t.version != body.version:
        raise Conflict("Task başka biri tarafından güncellendi. Sayfayı yenileyin.")
    fields = body.model_fields_set - {"version", "collaborator_ids"}
    before = _snapshot(t)
    old_collabs = {u.id for u in t.collaborators}
    for name in fields:
        value = getattr(body, name)
        if name in ("title", "priority", "category", "recurrence") and value is None:
            raise BadRequest(errors=[{"field": name, "message": "Boş olamaz."}])
        setattr(t, name, value)
    collabs = (
        list(dict.fromkeys(body.collaborator_ids or []))
        if "collaborator_ids" in body.model_fields_set
        else [u.id for u in t.collaborators]
    )
    changed = {k for k in fields} | ({"collaborators"} if set(collabs) != old_collabs else set())
    _check_people(db, user, t.team_id, t.assignee_id, t.backup_assignee_id, collabs, t.requester_id, changed)
    if "collaborators" in changed:
        _set_collaborators(db, t, collabs)
    changes = diff(before, _snapshot(t))
    if changes:
        t.version += 1
        record(db, "task.update", "task", t.id, changes)
        if "backup_assignee_id" in changes:
            _add_watchers(db, t.id, [t.backup_assignee_id])
        _notify_assignment(
            db, t, user, "assignee_id" in changes, "backup_assignee_id" in changes, set(collabs) - old_collabs
        )
        notify(
            db,
            _audience(db, t),
            NT.TASK_UPDATED,
            f"{user.full_name} task'ı güncelledi: {t.title}",
            body=f"Değişen: {_change_summary(changes)}",
            entity_type="task",
            entity_id=t.id,
            actor_id=user.id,
        )
    db.flush()
    db.refresh(t)
    return _one(db, user, t)


def delete_task(db: Session, user: User, task_id: UUID) -> None:
    t = repo.get_visible(db, user, task_id)
    P.require(P.can_delete_task(db, user, t), user, "task.delete", str(t.id))
    t.deleted_at = utcnow()
    record(db, "task.delete", "task", t.id)


def _progress_entry(db: Session, t: Task, user: User, to: int, note: str) -> None:
    db.add(
        TaskProgressEntry(
            task_id=t.id, author_id=user.id, from_progress=t.progress, to_progress=to, note=note
        )
    )
    t.progress = to


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
        if t.progress != 100:
            _progress_entry(db, t, user, 100, "Task tamamlandı.")
    if frm == TaskStatus.DONE:
        t.completed_at = None
    t.blocked_reason = reason if to == TaskStatus.BLOCKED else None
    t.version += 1
    record(db, "task.transition", "task", t.id, {"status": [frm.value, to.value]})
    metrics.TASK_TRANSITIONS.labels(frm.value, to.value).inc()
    manager_id = t.team.manager_id if t.team else None
    notify(
        db,
        _audience(db, t, t.created_by, t.requester_id, manager_id, t.assignee_id),
        NT.TASK_STATUS_CHANGED,
        f"{user.full_name} durumu değiştirdi: {t.title} → {STATUS_TR[to]}",
        body=reason or None,
        entity_type="task",
        entity_id=t.id,
        actor_id=user.id,
    )
    db.flush()
    db.refresh(t)
    return _one(db, user, t)


# ------------------------------------------------------------------ ilerleme (timeline)
def update_progress(db: Session, user: User, task_id: UUID, body: c.TaskProgressUpdate) -> c.Task:
    t = repo.get_visible(db, user, task_id)
    P.require(P.can_update_progress(db, user, t), user, "task.progress", str(t.id))
    if t.version != body.version:
        raise Conflict("Task başka biri tarafından güncellendi. Sayfayı yenileyin.")
    note = body.note.strip()
    if not note:
        raise BadRequest(errors=[{"field": "note", "message": "Kısa bir not zorunlu."}])
    if body.progress == t.progress:
        raise BadRequest(errors=[{"field": "progress", "message": "İlerleme değişmedi."}])
    frm = t.progress
    _progress_entry(db, t, user, body.progress, note)
    if t.status == TaskStatus.TODO and body.progress > 0:
        t.status = TaskStatus.IN_PROGRESS
        t.started_at = t.started_at or utcnow()
    t.version += 1
    record(db, "task.progress", "task", t.id, {"progress": [frm, body.progress]})
    manager_id = t.team.manager_id if t.team else None
    notify(
        db,
        _audience(db, t, t.requester_id, manager_id, t.assignee_id),
        NT.TASK_PROGRESS,
        f"{user.full_name} ilerlemeyi %{body.progress} yaptı: {note}",
        body=f"{t.title} (%{frm} → %{body.progress})",
        entity_type="task",
        entity_id=t.id,
        actor_id=user.id,
    )
    db.flush()
    db.refresh(t)
    return _one(db, user, t)


def list_progress(db: Session, user: User, task_id: UUID) -> list[c.ProgressEntry]:
    t = repo.get_visible(db, user, task_id)
    rows = db.scalars(
        select(TaskProgressEntry)
        .where(TaskProgressEntry.task_id == t.id)
        .order_by(TaskProgressEntry.created_at, TaskProgressEntry.id)
    )
    return [
        c.ProgressEntry(
            id=e.id,
            task_id=e.task_id,
            author=user_ref(e.author),  # type: ignore[arg-type]
            from_progress=e.from_progress,
            to_progress=e.to_progress,
            note=e.note,
            created_at=e.created_at,
        )
        for e in rows
    ]


# ------------------------------------------------------------------ takip (yıldız)
def watch(db: Session, user: User, task_id: UUID, on: bool) -> None:
    t = repo.get_visible(db, user, task_id)
    if on:
        _add_watchers(db, t.id, [user.id])
    else:
        db.execute(delete(TaskWatcher).where(TaskWatcher.task_id == t.id, TaskWatcher.user_id == user.id))


def list_watchers(db: Session, user: User, task_id: UUID) -> list[c.UserRef]:
    t = repo.get_visible(db, user, task_id)
    rows = db.scalars(
        select(User)
        .join(TaskWatcher, TaskWatcher.user_id == User.id)
        .where(TaskWatcher.task_id == t.id)
        .order_by(User.full_name)
    )
    return [c.UserRef(id=u.id, full_name=u.full_name) for u in rows.unique()]


# ------------------------------------------------------------------ yorumlar ve geçmiş
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
        _audience(db, t, t.assignee_id, t.backup_assignee_id, t.created_by, t.requester_id),
        NT.TASK_COMMENTED,
        f"{user.full_name} yorum yaptı: {t.title}",
        body=text[:300],
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


# ------------------------------------------------------------------ ekler
def _attachment(a: Attachment) -> c.Attachment:
    return c.Attachment(
        id=a.id,
        task_id=a.task_id,
        file_name=a.file_name,
        content_type=a.content_type,
        size_bytes=a.size_bytes,
        uploaded_by=user_ref(a.uploader),  # type: ignore[arg-type]
        created_at=a.created_at,
    )


def safe_file_name(name: str | None) -> str:
    base = (name or "dosya").replace("\\", "/").rsplit("/", 1)[-1]
    cleaned = "".join(ch for ch in base if ch.isprintable() and ch not in '<>:"|?*').strip(" .")
    return (cleaned or "dosya")[:255]


def check_upload(data: bytes, content_type: str | None, allowed: tuple[str, ...] | None = None) -> str:
    limit = get_settings().max_upload_bytes
    if not data:
        raise BadRequest(errors=[{"field": "file", "message": "Dosya boş."}])
    if len(data) > limit:
        raise BadRequest(
            errors=[{"field": "file", "message": f"Dosya en fazla {limit // (1024 * 1024)} MB olabilir."}]
        )
    ctype = (content_type or "application/octet-stream").split(";")[0].strip().lower()
    if allowed is not None:
        ok = ctype in allowed
    else:
        ok = ctype.startswith(ALLOWED_MIME_PREFIXES) or ctype in ALLOWED_MIME_EXACT
    if not ok or ctype in ("text/html", "image/svg+xml"):
        raise BadRequest(errors=[{"field": "file", "message": "Bu dosya türü desteklenmiyor."}])
    return ctype


def list_attachments(db: Session, user: User, task_id: UUID) -> list[c.Attachment]:
    t = repo.get_visible(db, user, task_id)
    rows = db.scalars(
        select(Attachment)
        .where(Attachment.task_id == t.id, Attachment.deleted_at.is_(None))
        .order_by(Attachment.created_at)
    )
    return [_attachment(a) for a in rows.unique()]


def add_attachment(
    db: Session, user: User, task_id: UUID, file_name: str | None, content_type: str | None, data: bytes
) -> c.Attachment:
    t = repo.get_visible(db, user, task_id)
    P.require(P.can_attach(db, user, t), user, "attachment.create", str(t.id))
    ctype = check_upload(data, content_type)
    a = Attachment(
        task_id=t.id,
        file_name=safe_file_name(file_name),
        content_type=ctype,
        size_bytes=len(data),
        sha256=hashlib.sha256(data).hexdigest(),
        data=data,
        uploaded_by=user.id,
    )
    db.add(a)
    db.flush()
    record(db, "attachment.create", "task", t.id, {"attachment": [None, a.file_name]})
    notify(
        db,
        _audience(db, t, t.assignee_id),
        NT.TASK_UPDATED,
        f"{user.full_name} ek ekledi: {t.title}",
        body=a.file_name,
        entity_type="task",
        entity_id=t.id,
        actor_id=user.id,
    )
    db.refresh(a)
    return _attachment(a)


def _visible_attachment(db: Session, user: User, attachment_id: UUID) -> tuple[Attachment, Task]:
    a = db.get(Attachment, attachment_id)
    if a is None or a.deleted_at is not None:
        raise NotFound("Ek bulunamadı.")
    return a, repo.get_visible(db, user, a.task_id)


def download_attachment(db: Session, user: User, attachment_id: UUID) -> Attachment:
    a, _ = _visible_attachment(db, user, attachment_id)
    return a


def delete_attachment(db: Session, user: User, attachment_id: UUID) -> None:
    a, t = _visible_attachment(db, user, attachment_id)
    allowed = a.uploaded_by == user.id or P.can_update_task(db, user, t)
    P.require(allowed and user.role != Role.AUDITOR, user, "attachment.delete", str(a.id))
    a.deleted_at = utcnow()
    record(db, "attachment.delete", "task", t.id, {"attachment": [a.file_name, None]})


# ------------------------------------------------------------------ atanabilir kişiler ve öneri
def assignable_users(db: Session, user: User, team_id: UUID | None) -> list[c.AssignableUser]:
    q = select(User).where(assignable_filter(db, user))
    if team_id is not None:
        # Ekibe göre süz: ekip üyeleri + ekibin yöneticisi + (direktör için) unit yöneticileri
        team = db.get(Team, team_id)
        conds = [User.team_id == team_id]
        if team is not None and team.manager_id:
            conds.append(User.id == team.manager_id)
        if user.role == Role.DIRECTOR:
            conds.append(User.role == Role.UNIT_MANAGER)
        q = q.where(or_(*conds))
    order = {Role.UNIT_MANAGER: 0, Role.MANAGER: 1, Role.DIRECTOR: 2, Role.EMPLOYEE: 3}
    users = sorted(db.scalars(q).unique(), key=lambda u: (order.get(u.role, 9), u.full_name))
    return [
        c.AssignableUser(
            id=u.id,
            full_name=u.full_name,
            title=u.title,
            role=u.role,
            team_id=u.team_id,
            team_name=u.team.name if u.team else None,
        )
        for u in users
    ]


def suggest_assignees(
    db: Session, user: User, category: c.TaskCategory, team_id: UUID | None
) -> list[c.AssigneeSuggestion]:
    from app.modules.competencies.service import scores_for_category

    people = [
        u
        for u in assignable_users(db, user, team_id)
        if u.role in (Role.EMPLOYEE, Role.MANAGER, Role.UNIT_MANAGER)
    ]
    if not people:
        return []
    scored = scores_for_category(db, [p.id for p in people], category)
    out = []
    for p in people:
        avg, comps = scored.get(p.id, (0, []))
        if avg > 0:
            out.append(c.AssigneeSuggestion(user=p, score=avg, competencies=comps))
    out.sort(key=lambda s: (-s.score, s.user.full_name))
    return out[:5]
