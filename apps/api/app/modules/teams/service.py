"""Ekipler — oluşturma/güncelleme sadece direktör; yönetici rolü MANAGER olmalı."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import contract as c
from app.audit.service import diff, record
from app.auth import policies as P
from app.auth.scope import in_scope, team_filter, visible_team_ids
from app.contract import Role
from app.core.errors import BadRequest, Conflict, NotFound
from app.core.schemas import user_ref
from app.models import Team, User


def _member_counts(db: Session) -> dict[UUID, int]:
    rows = db.execute(
        select(User.team_id, func.count()).where(User.is_active.is_(True)).group_by(User.team_id)
    )
    return {tid: n for tid, n in rows if tid}


def to_contract(t: Team, count: int) -> c.Team:
    return c.Team(
        id=t.id, name=t.name, description=t.description, manager=user_ref(t.manager), member_count=count
    )


def list_teams(db: Session, user: User) -> list[c.Team]:
    counts = _member_counts(db)
    rows = db.scalars(
        select(Team).where(team_filter(Team.id, visible_team_ids(db, user))).order_by(Team.name)
    )
    return [to_contract(t, counts.get(t.id, 0)) for t in rows.unique()]


def get_visible(db: Session, user: User, team_id: UUID) -> Team:
    t = db.get(Team, team_id)
    if t is None or not in_scope(t.id, visible_team_ids(db, user)):
        raise NotFound("Ekip bulunamadı.")
    return t


def get(db: Session, user: User, team_id: UUID) -> c.Team:
    t = get_visible(db, user, team_id)
    return to_contract(t, _member_counts(db).get(t.id, 0))


def _check_manager(db: Session, manager_id: UUID | None) -> None:
    if manager_id is None:
        return
    m = db.get(User, manager_id)
    if m is None or not m.is_active or m.role != Role.MANAGER:
        raise BadRequest(errors=[{"field": "managerId", "message": "Aktif bir yönetici seçilmeli."}])


def create(db: Session, user: User, body: c.TeamCreate) -> c.Team:
    P.require(P.can_manage_users(user), user, "team.create")
    _check_manager(db, body.manager_id)
    t = Team(name=body.name.strip(), description=body.description, manager_id=body.manager_id)
    db.add(t)
    try:
        db.flush()
    except IntegrityError as exc:
        raise Conflict("Bu adla bir ekip zaten var.") from exc
    record(db, "team.create", "team", t.id, {"name": [None, t.name]})
    db.refresh(t)
    return to_contract(t, 0)


def update(db: Session, user: User, team_id: UUID, body: c.TeamUpdate) -> c.Team:
    t = get_visible(db, user, team_id)
    P.require(P.can_manage_users(user), user, "team.update", str(t.id))
    before = {"name": t.name, "description": t.description, "manager_id": t.manager_id}
    for name in body.model_fields_set:
        value = getattr(body, name)
        if name == "name" and not value:
            raise BadRequest(errors=[{"field": "name", "message": "Boş olamaz."}])
        setattr(t, name, value)
    _check_manager(db, t.manager_id)
    try:
        db.flush()
    except IntegrityError as exc:
        raise Conflict("Bu adla bir ekip zaten var.") from exc
    changes = diff(before, {"name": t.name, "description": t.description, "manager_id": t.manager_id})
    if changes:
        record(db, "team.update", "team", t.id, changes)
    db.refresh(t)
    return to_contract(t, _member_counts(db).get(t.id, 0))
