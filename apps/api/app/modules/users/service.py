"""Kullanıcı yönetimi — rol/ekip/aktiflik sadece direktör; kendi rolünü değiştiremez (AUT-04)."""

from uuid import UUID

from sqlalchemy import delete, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import contract as c
from app.audit.service import diff, record
from app.auth import policies as P
from app.auth.passwords import hash_password
from app.auth.scope import team_filter, visible_team_ids
from app.contract import Role
from app.core.errors import BadRequest, Conflict, NotFound
from app.core.schemas import PageParams, to_user
from app.models import Team, User, UserSession
from app.modules.tasks.repository import escape_like
from app.security_events.service import emit

TEAMLESS_ROLES = (Role.DIRECTOR, Role.AUDITOR)


def get_visible(db: Session, user: User, user_id: UUID) -> User:
    target = db.get(User, user_id)
    if target is None or not P.can_read_user(db, user, target):
        raise NotFound("Kullanıcı bulunamadı.")
    return target


def list_users(
    db: Session,
    user: User,
    pp: PageParams,
    q: str | None,
    team_id: UUID | None,
    role: Role | None,
    is_active: bool | None,
) -> c.UserPage:
    stmt = select(User)
    if user.role not in TEAMLESS_ROLES:
        stmt = stmt.where(or_(team_filter(User.team_id, visible_team_ids(db, user)), User.id == user.id))
    if q:
        pat = f"%{escape_like(q)}%"
        stmt = stmt.where(or_(User.full_name.ilike(pat, escape="\\"), User.email.ilike(pat, escape="\\")))
    if team_id:
        stmt = stmt.where(User.team_id == team_id)
    if role:
        stmt = stmt.where(User.role == role)
    if is_active is not None:
        stmt = stmt.where(User.is_active.is_(is_active))
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.order_by(User.full_name).offset(pp.offset).limit(pp.page_size)).unique()
    return c.UserPage(items=[to_user(u) for u in rows], total=total, page=pp.page, page_size=pp.page_size)


def _validate_team(db: Session, role: Role, team_id: UUID | None) -> None:
    if role in TEAMLESS_ROLES:
        return
    if team_id is None:
        raise BadRequest(errors=[{"field": "teamId", "message": "Çalışan ve yönetici için ekip zorunlu."}])
    if db.get(Team, team_id) is None:
        raise BadRequest(errors=[{"field": "teamId", "message": "Ekip bulunamadı."}])


def create(db: Session, user: User, body: c.UserCreate) -> c.User:
    P.require(P.can_manage_users(user), user, "user.create")
    _validate_team(db, body.role, body.team_id)
    u = User(
        email=str(body.email).lower(),
        full_name=body.full_name.strip(),
        title=body.title,
        role=body.role,
        team_id=None if body.role in TEAMLESS_ROLES else body.team_id,
        password_hash=hash_password(body.password),
    )
    db.add(u)
    try:
        db.flush()
    except IntegrityError as exc:
        raise Conflict("Bu e-posta ile bir kullanıcı zaten var.") from exc
    record(db, "user.create", "user", u.id, {"email": [None, u.email], "role": [None, u.role.value]})
    db.refresh(u)
    return to_user(u)


def update(db: Session, user: User, user_id: UUID, body: c.UserUpdate) -> c.User:
    target = get_visible(db, user, user_id)
    fields = body.model_fields_set
    privileged = fields & {"role", "team_id", "is_active"}
    if privileged:
        P.require(P.can_manage_users(user), user, "user.update", str(target.id))
        if "role" in fields and body.role != target.role:
            P.require(P.can_change_role(user, target), user, "user.role_change", str(target.id))
        if "is_active" in fields and target.id == user.id:
            P.require(False, user, "user.deactivate_self", str(target.id))
    elif target.id != user.id:
        P.require(P.can_manage_users(user), user, "user.update", str(target.id))
    before = {
        "full_name": target.full_name,
        "title": target.title,
        "role": target.role,
        "team_id": target.team_id,
        "is_active": target.is_active,
    }
    for name in fields:
        value = getattr(body, name)
        if name in ("full_name", "role", "is_active") and value is None:
            raise BadRequest(errors=[{"field": name, "message": "Boş olamaz."}])
        setattr(target, name, value)
    if target.role in TEAMLESS_ROLES:
        target.team_id = None
    _validate_team(db, target.role, target.team_id)
    after = {
        "full_name": target.full_name,
        "title": target.title,
        "role": target.role,
        "team_id": target.team_id,
        "is_active": target.is_active,
    }
    changes = diff(before, after)
    if not changes:
        return to_user(target)
    if "role" in changes:
        record(db, "user.role_change", "user", target.id, {"role": changes["role"]})
        emit(
            "ROLE_CHANGED",
            details={"target": str(target.id), "from": changes["role"][0], "to": changes["role"][1]},
        )
        if target.role != Role.MANAGER:  # yönetici değilse yönettiği ekiplerden çıkar
            for team in db.scalars(select(Team).where(Team.manager_id == target.id)):
                team.manager_id = None
    if "is_active" in changes and not target.is_active:
        db.execute(delete(UserSession).where(UserSession.user_id == target.id))
        record(db, "user.deactivate", "user", target.id)
        emit("USER_DEACTIVATED", details={"target": str(target.id)})
    record(db, "user.update", "user", target.id, changes)
    db.flush()
    db.refresh(target)
    return to_user(target)
