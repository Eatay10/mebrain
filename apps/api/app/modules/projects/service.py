"""Projeler — ilerleme, task durum sayımlarından hesaplanır (PRJ-02)."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import contract as c
from app.audit.service import diff, record
from app.auth import policies as P
from app.auth.scope import in_scope, team_filter, visible_team_ids
from app.contract import TaskStatus
from app.core.errors import BadRequest, Conflict, NotFound
from app.core.schemas import PageParams, user_ref
from app.models import Project, Task, Team, User
from app.models.base import utcnow
from app.modules.tasks import counting
from app.security_events.service import emit

TRACKED = ("name", "description", "owner_id", "status", "start_date", "due_date")


def to_contract(p: Project, progress: c.StatusCounts | None = None) -> c.Project:
    return c.Project(
        id=p.id,
        team_id=p.team_id,
        team_name=p.team.name if p.team else None,
        name=p.name,
        description=p.description,
        owner=user_ref(p.owner),
        status=p.status,
        start_date=p.start_date,
        due_date=p.due_date,
        progress=progress or counting.empty(),
        created_at=p.created_at,
    )


def progress_for(db: Session, ids: list[UUID]) -> dict[UUID, c.StatusCounts]:
    if not ids:
        return {}
    by = counting.counts_by(db, [Task.project_id], [Task.project_id.in_(ids)])
    return {k[0]: v for k, v in by.items()}


def get_visible(db: Session, user: User, project_id: UUID) -> Project:
    p = db.get(Project, project_id)
    if p is None or p.deleted_at is not None:
        raise NotFound("Proje bulunamadı.")
    if not P.can_read_project(db, user, p):
        emit("NOT_FOUND_PROBE", user_id=user.id, details={"entity": "project"})
        raise NotFound("Proje bulunamadı.")
    return p


def get(db: Session, user: User, project_id: UUID) -> c.Project:
    p = get_visible(db, user, project_id)
    return to_contract(p, progress_for(db, [p.id]).get(p.id))


def list_projects(
    db: Session,
    user: User,
    pp: PageParams,
    q: str | None,
    team_id: UUID | None,
    status: c.ProjectStatus | None,
) -> c.ProjectPage:
    stmt = select(Project).where(
        Project.deleted_at.is_(None), team_filter(Project.team_id, visible_team_ids(db, user))
    )
    if q:
        from app.modules.tasks.repository import escape_like

        stmt = stmt.where(Project.name.ilike(f"%{escape_like(q)}%", escape="\\"))
    if team_id:
        stmt = stmt.where(Project.team_id == team_id)
    if status:
        stmt = stmt.where(Project.status == status)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = list(
        db.scalars(
            stmt.order_by(Project.due_date.asc().nulls_last(), Project.name)
            .offset(pp.offset)
            .limit(pp.page_size)
        ).unique()
    )
    prog = progress_for(db, [p.id for p in rows])
    return c.ProjectPage(
        items=[to_contract(p, prog.get(p.id)) for p in rows],
        total=total,
        page=pp.page,
        page_size=pp.page_size,
    )


def _check_owner(db: Session, team_id: UUID, owner_id: UUID | None) -> None:
    if owner_id is None:
        return
    o = db.get(User, owner_id)
    if o is None or not o.is_active:
        raise BadRequest(errors=[{"field": "ownerId", "message": "Geçersiz kullanıcı."}])
    team = db.get(Team, team_id)
    if o.team_id != team_id and (team is None or team.manager_id != o.id):
        raise BadRequest(
            errors=[{"field": "ownerId", "message": "Sahip ekibin üyesi veya yöneticisi olmalı."}]
        )


def _check_dates(p: Project) -> None:
    if p.start_date and p.due_date and p.due_date < p.start_date:
        raise BadRequest(errors=[{"field": "dueDate", "message": "Bitiş, başlangıçtan önce olamaz."}])


def create(db: Session, user: User, body: c.ProjectCreate) -> c.Project:
    if db.get(Team, body.team_id) is None or not in_scope(body.team_id, visible_team_ids(db, user)):
        raise NotFound("Ekip bulunamadı.")
    P.require(P.can_manage_project(db, user, body.team_id), user, "project.create")
    _check_owner(db, body.team_id, body.owner_id)
    p = Project(
        team_id=body.team_id,
        name=body.name.strip(),
        description=body.description,
        owner_id=body.owner_id,
        start_date=body.start_date,
        due_date=body.due_date,
        created_by=user.id,
    )
    _check_dates(p)
    db.add(p)
    try:
        db.flush()
    except IntegrityError as exc:
        raise Conflict("Bu ekipte aynı adlı bir proje var.") from exc
    record(db, "project.create", "project", p.id, diff({}, {k: getattr(p, k) for k in TRACKED}))
    db.refresh(p)
    return to_contract(p)


def update(db: Session, user: User, project_id: UUID, body: c.ProjectUpdate) -> c.Project:
    p = get_visible(db, user, project_id)
    P.require(P.can_manage_project(db, user, p.team_id), user, "project.update", str(p.id))
    before = {k: getattr(p, k) for k in TRACKED}
    for name in body.model_fields_set:
        value = getattr(body, name)
        if name in ("name", "status") and value is None:
            raise BadRequest(errors=[{"field": name, "message": "Boş olamaz."}])
        setattr(p, name, value.strip() if name == "name" else value)
    _check_owner(db, p.team_id, p.owner_id)
    _check_dates(p)
    try:
        db.flush()
    except IntegrityError as exc:
        raise Conflict("Bu ekipte aynı adlı bir proje var.") from exc
    changes = diff(before, {k: getattr(p, k) for k in TRACKED})
    if changes:
        record(db, "project.update", "project", p.id, changes)
    db.refresh(p)
    return to_contract(p, progress_for(db, [p.id]).get(p.id))


def delete(db: Session, user: User, project_id: UUID) -> None:
    p = get_visible(db, user, project_id)
    P.require(P.can_manage_project(db, user, p.team_id), user, "project.delete", str(p.id))
    open_tasks = (
        db.scalar(
            select(func.count()).where(
                Task.project_id == p.id, Task.deleted_at.is_(None), Task.status != TaskStatus.DONE
            )
        )
        or 0
    )
    if open_tasks:
        raise Conflict(f"Projede {open_tasks} açık task var; önce tamamlayın veya silin.")
    p.deleted_at = utcnow()
    record(db, "project.delete", "project", p.id)
