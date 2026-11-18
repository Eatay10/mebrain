"""Ekipler ve unit'ler — oluşturma/güncelleme sadece direktör.

Ekip yöneticisi MANAGER veya UNIT_MANAGER, unit yöneticisi UNIT_MANAGER rolünde olmalı.
"""

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
from app.models import Team, Unit, User


def _member_counts(db: Session) -> dict[UUID, int]:
    rows = db.execute(
        select(User.team_id, func.count()).where(User.is_active.is_(True)).group_by(User.team_id)
    )
    return {tid: n for tid, n in rows if tid}


def to_contract(t: Team, count: int) -> c.Team:
    return c.Team(
        id=t.id,
        name=t.name,
        description=t.description,
        manager=user_ref(t.manager),
        member_count=count,
        unit_id=t.unit_id,
        unit_name=t.unit.name if t.unit else None,
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
    if m is None or not m.is_active or m.role not in (Role.MANAGER, Role.UNIT_MANAGER):
        raise BadRequest(errors=[{"field": "managerId", "message": "Aktif bir yönetici seçilmeli."}])


def _check_unit(db: Session, unit_id: UUID | None) -> None:
    if unit_id is not None and db.get(Unit, unit_id) is None:
        raise BadRequest(errors=[{"field": "unitId", "message": "Unit bulunamadı."}])


def create(db: Session, user: User, body: c.TeamCreate) -> c.Team:
    P.require(P.can_manage_users(user), user, "team.create")
    _check_manager(db, body.manager_id)
    _check_unit(db, body.unit_id)
    t = Team(
        name=body.name.strip(), description=body.description, manager_id=body.manager_id, unit_id=body.unit_id
    )
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
    before = {"name": t.name, "description": t.description, "manager_id": t.manager_id, "unit_id": t.unit_id}
    for name in body.model_fields_set:
        value = getattr(body, name)
        if name == "name" and not value:
            raise BadRequest(errors=[{"field": "name", "message": "Boş olamaz."}])
        setattr(t, name, value)
    _check_manager(db, t.manager_id)
    _check_unit(db, t.unit_id)
    try:
        db.flush()
    except IntegrityError as exc:
        raise Conflict("Bu adla bir ekip zaten var.") from exc
    after = {"name": t.name, "description": t.description, "manager_id": t.manager_id, "unit_id": t.unit_id}
    changes = diff(before, after)
    if changes:
        record(db, "team.update", "team", t.id, changes)
    db.refresh(t)
    return to_contract(t, _member_counts(db).get(t.id, 0))


# ------------------------------------------------------------------ units
def unit_to_contract(u: Unit, team_count: int) -> c.Unit:
    return c.Unit(
        id=u.id, name=u.name, description=u.description, manager=user_ref(u.manager), team_count=team_count
    )


def _team_counts(db: Session) -> dict[UUID, int]:
    rows = db.execute(
        select(Team.unit_id, func.count()).where(Team.unit_id.is_not(None)).group_by(Team.unit_id)
    )
    return {uid: n for uid, n in rows}


def list_units(db: Session, user: User) -> list[c.Unit]:
    counts = _team_counts(db)
    return [
        unit_to_contract(u, counts.get(u.id, 0))
        for u in db.scalars(select(Unit).order_by(Unit.name)).unique()
    ]


def _check_unit_manager(db: Session, manager_id: UUID | None) -> None:
    if manager_id is None:
        return
    m = db.get(User, manager_id)
    if m is None or not m.is_active or m.role != Role.UNIT_MANAGER:
        raise BadRequest(errors=[{"field": "managerId", "message": "Aktif bir unit yöneticisi seçilmeli."}])


def create_unit(db: Session, user: User, body: c.UnitCreate) -> c.Unit:
    P.require(P.can_manage_units(user), user, "unit.create")
    _check_unit_manager(db, body.manager_id)
    u = Unit(name=body.name.strip(), description=body.description, manager_id=body.manager_id)
    db.add(u)
    try:
        db.flush()
    except IntegrityError as exc:
        raise Conflict("Bu adla bir unit zaten var.") from exc
    record(db, "unit.create", "unit", u.id, {"name": [None, u.name]})
    db.refresh(u)
    return unit_to_contract(u, 0)


def update_unit(db: Session, user: User, unit_id: UUID, body: c.UnitUpdate) -> c.Unit:
    P.require(P.can_manage_units(user), user, "unit.update")
    u = db.get(Unit, unit_id)
    if u is None:
        raise NotFound("Unit bulunamadı.")
    before = {"name": u.name, "description": u.description, "manager_id": u.manager_id}
    for name in body.model_fields_set:
        value = getattr(body, name)
        if name == "name" and not value:
            raise BadRequest(errors=[{"field": "name", "message": "Boş olamaz."}])
        setattr(u, name, value)
    _check_unit_manager(db, u.manager_id)
    try:
        db.flush()
    except IntegrityError as exc:
        raise Conflict("Bu adla bir unit zaten var.") from exc
    changes = diff(before, {"name": u.name, "description": u.description, "manager_id": u.manager_id})
    if changes:
        record(db, "unit.update", "unit", u.id, changes)
    db.refresh(u)
    return unit_to_contract(u, _team_counts(db).get(u.id, 0))
