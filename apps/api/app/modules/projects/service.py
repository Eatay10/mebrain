"""Projeler — ilerleme, task durum sayımlarından hesaplanır (PRJ-02)."""

from uuid import UUID

from sqlalchemy import delete as sa_delete
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import contract as c
from app.audit.service import diff, record
from app.auth import policies as P
from app.auth.scope import in_scope, team_filter, visible_team_ids
from app.contract import OrgNodeKind, Role, StakeholderRole, TaskStatus
from app.core.errors import BadRequest, Conflict, NotFound
from app.core.schemas import PageParams, user_ref
from app.models import Project, ProjectStakeholder, ProjectWatcher, Task, TaskCollaborator, Team, Unit, User
from app.models.base import utcnow
from app.modules.tasks import counting
from app.security_events.service import emit

TRACKED = ("name", "description", "owner_id", "status", "start_date", "due_date")


def to_contract(p: Project, progress: c.StatusCounts | None = None, watching: bool = False) -> c.Project:
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
        is_watching=watching,
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


def watched_ids(db: Session, user: User, ids: list[UUID]) -> set[UUID]:
    if not ids:
        return set()
    return set(
        db.scalars(
            select(ProjectWatcher.project_id).where(
                ProjectWatcher.user_id == user.id, ProjectWatcher.project_id.in_(ids)
            )
        )
    )


def watch(db: Session, user: User, project_id: UUID, on: bool) -> None:
    """Yıldız kişiseldir: projeyi görebilen herkes (denetmen dahil) koyabilir."""
    p = get_visible(db, user, project_id)
    if on:
        db.execute(
            insert(ProjectWatcher)
            .values(project_id=p.id, user_id=user.id, created_at=utcnow())
            .on_conflict_do_nothing()
        )
    else:
        db.execute(
            sa_delete(ProjectWatcher).where(
                ProjectWatcher.project_id == p.id, ProjectWatcher.user_id == user.id
            )
        )


def get(db: Session, user: User, project_id: UUID) -> c.Project:
    p = get_visible(db, user, project_id)
    return to_contract(p, progress_for(db, [p.id]).get(p.id), p.id in watched_ids(db, user, [p.id]))


def list_projects(
    db: Session,
    user: User,
    pp: PageParams,
    q: str | None,
    team_id: UUID | None,
    status: c.ProjectStatus | None,
    watching: bool | None = None,
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
    if watching:
        stmt = stmt.where(
            Project.id.in_(select(ProjectWatcher.project_id).where(ProjectWatcher.user_id == user.id))
        )
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = list(
        db.scalars(
            stmt.order_by(Project.due_date.asc().nulls_last(), Project.name)
            .offset(pp.offset)
            .limit(pp.page_size)
        ).unique()
    )
    prog = progress_for(db, [p.id for p in rows])
    starred = watched_ids(db, user, [p.id for p in rows])
    return c.ProjectPage(
        items=[to_contract(p, prog.get(p.id), p.id in starred) for p in rows],
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


# ------------------------------------------------------------------ paydaşlar ve organizasyon ağacı
STAKEHOLDER_TR = {
    StakeholderRole.SPONSOR: "Sponsor",
    StakeholderRole.OWNER: "Sahip",
    StakeholderRole.LEAD: "Proje lideri",
    StakeholderRole.MEMBER: "Proje üyesi",
    StakeholderRole.STAKEHOLDER: "Paydaş",
    StakeholderRole.OBSERVER: "Gözlemci",
}


def _stakeholder(sh: ProjectStakeholder) -> c.ProjectStakeholder:
    return c.ProjectStakeholder(
        id=sh.id,
        user=user_ref(sh.user),
        name=sh.user.full_name if sh.user else (sh.name or ""),
        organization=sh.organization if sh.user is None else (sh.user.team.name if sh.user.team else None),
        role=sh.role,
        note=sh.note,
    )


def add_stakeholder(
    db: Session, user: User, project_id: UUID, body: c.ProjectStakeholderCreate
) -> c.ProjectStakeholder:
    p = get_visible(db, user, project_id)
    P.require(P.can_manage_project(db, user, p.team_id), user, "project.stakeholder", str(p.id))
    if body.user_id is None and not (body.name or "").strip():
        raise BadRequest(errors=[{"field": "name", "message": "Kurum içi kişi veya dış paydaş adı gerekli."}])
    if body.user_id is not None:
        target = db.get(User, body.user_id)
        if target is None or not target.is_active:
            raise BadRequest(errors=[{"field": "userId", "message": "Aktif bir kullanıcı seçilmeli."}])
    sh = ProjectStakeholder(
        project_id=p.id,
        user_id=body.user_id,
        name=None if body.user_id else body.name.strip(),  # type: ignore[union-attr]
        organization=None if body.user_id else body.organization,
        role=body.role,
        note=body.note,
    )
    db.add(sh)
    try:
        db.flush()
    except IntegrityError as exc:
        raise Conflict("Bu kişi bu rolle zaten paydaş.") from exc
    record(
        db, "project.stakeholder_add", "project", p.id, {"stakeholder": [None, sh.name or str(sh.user_id)]}
    )
    db.refresh(sh)
    return _stakeholder(sh)


def remove_stakeholder(db: Session, user: User, project_id: UUID, stakeholder_id: UUID) -> None:
    p = get_visible(db, user, project_id)
    P.require(P.can_manage_project(db, user, p.team_id), user, "project.stakeholder", str(p.id))
    sh = db.get(ProjectStakeholder, stakeholder_id)
    if sh is None or sh.project_id != p.id:
        raise NotFound("Paydaş bulunamadı.")
    record(
        db, "project.stakeholder_remove", "project", p.id, {"stakeholder": [sh.name or str(sh.user_id), None]}
    )
    db.delete(sh)


def organization(db: Session, user: User, project_id: UUID) -> c.ProjectOrganization:
    """Projede yer alan kişileri (sahip, sorumlular, yedekler, çalışma arkadaşları, talep sahipleri, kurum içi
    paydaşlar) ve üst zincirlerini Direktör → Unit → Ekip → Kişi ağacında döner."""
    p = get_visible(db, user, project_id)
    roles: dict[UUID, set[str]] = {}

    def add(uid: UUID | None, label: str) -> None:
        if uid:
            roles.setdefault(uid, set()).add(label)

    add(p.owner_id, "Proje sahibi")
    tasks = list(db.scalars(select(Task).where(Task.project_id == p.id, Task.deleted_at.is_(None))).unique())
    for t in tasks:
        add(t.assignee_id, "Sorumlu")
        add(t.backup_assignee_id, "Yedek sorumlu")
        add(t.requester_id, "Talep sahibi")
    if tasks:
        for uid in db.scalars(
            select(TaskCollaborator.user_id).where(TaskCollaborator.task_id.in_([t.id for t in tasks]))
        ):
            add(uid, "Çalışma arkadaşı")
    stakeholders = list(
        db.scalars(select(ProjectStakeholder).where(ProjectStakeholder.project_id == p.id)).unique()
    )
    for sh in stakeholders:
        add(sh.user_id, STAKEHOLDER_TR[sh.role])
    # Projenin ekibinin yöneticisi her zaman zincirde
    team = db.get(Team, p.team_id)
    if team and team.manager_id:
        add(team.manager_id, "Ekip yöneticisi")

    people = {u.id: u for u in db.scalars(select(User).where(User.id.in_(roles))).unique()} if roles else {}
    units = {u.id: u for u in db.scalars(select(Unit)).unique()}
    managed_unit = {u.manager_id: u.id for u in units.values() if u.manager_id}

    def node(
        kind: OrgNodeKind, id_: UUID, name: str, title: str | None, proles: list[str] | None = None
    ) -> c.OrgNode:
        return c.OrgNode(id=id_, kind=kind, name=name, title=title, project_roles=proles or [], children=[])

    def person(u: User) -> c.OrgNode:
        return node(OrgNodeKind.USER, u.id, u.full_name, u.title, sorted(roles.get(u.id, set())))

    directors = list(
        db.scalars(select(User).where(User.role == Role.DIRECTOR, User.is_active.is_(True))).unique()
    )
    root_children: list[c.OrgNode] = []
    unit_nodes: dict[UUID, c.OrgNode] = {}
    team_nodes: dict[UUID, c.OrgNode] = {}

    def unit_node(unit_id: UUID) -> c.OrgNode:
        if unit_id not in unit_nodes:
            u = units[unit_id]
            title = f"Unit yöneticisi: {u.manager.full_name}" if u.manager else None
            unit_nodes[unit_id] = node(OrgNodeKind.UNIT, u.id, u.name, title)
            root_children.append(unit_nodes[unit_id])
        return unit_nodes[unit_id]

    def team_node(t: Team) -> c.OrgNode:
        if t.id not in team_nodes:
            title = f"Yönetici: {t.manager.full_name}" if t.manager else None
            team_nodes[t.id] = node(OrgNodeKind.TEAM, t.id, t.name, title)
            (unit_node(t.unit_id).children if t.unit_id in units else root_children).append(team_nodes[t.id])
        return team_nodes[t.id]

    director_ids = {d.id for d in directors}
    for u in sorted(people.values(), key=lambda x: x.full_name):
        if u.id in director_ids:
            continue
        if u.role == Role.UNIT_MANAGER and u.id in managed_unit:
            unit_node(managed_unit[u.id]).children.insert(0, person(u))
        elif u.team is not None:
            team_node(u.team).children.append(person(u))
        else:
            root_children.append(person(u))
    tree = []
    for d in directors or []:
        dn = node(OrgNodeKind.DIRECTOR, d.id, d.full_name, d.title, sorted(roles.get(d.id, set())))
        tree.append(dn)
    if tree:
        tree[0].children = root_children
    else:
        tree = root_children
    return c.ProjectOrganization(
        project_id=p.id, tree=tree, stakeholders=[_stakeholder(x) for x in stakeholders]
    )
