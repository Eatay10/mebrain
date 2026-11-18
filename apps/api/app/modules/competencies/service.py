"""Yetkinlik kataloğu, kişisel seviyeler ve ekip matrisi (CMP-01, CMP-02, CMP-04)."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import contract as c
from app.audit.service import record
from app.auth import policies as P
from app.auth.scope import in_scope, visible_team_ids
from app.core.errors import Conflict, NotFound
from app.core.schemas import user_ref
from app.models import Competency, Team, User, UserCompetency
from app.models.base import utcnow
from app.modules.users.service import get_visible as get_visible_user


def _comp(cp: Competency) -> c.Competency:
    return c.Competency(id=cp.id, name=cp.name, category=cp.category, description=cp.description)


def _uc(uc: UserCompetency) -> c.UserCompetency:
    return c.UserCompetency(
        user_id=uc.user_id,
        competency=_comp(uc.competency),
        level=uc.level,
        evidence=uc.evidence,
        verified_by=user_ref(uc.verifier),
        verified_at=uc.verified_at,
        updated_at=uc.updated_at,
    )


def catalog(db: Session) -> list[c.Competency]:
    return [_comp(x) for x in db.scalars(select(Competency).order_by(Competency.category, Competency.name))]


def create(db: Session, user: User, body: c.CompetencyCreate) -> c.Competency:
    P.require(P.can_manage_catalog(user), user, "competency.create")
    cp = Competency(name=body.name.strip(), category=body.category, description=body.description)
    db.add(cp)
    try:
        db.flush()
    except IntegrityError as exc:
        raise Conflict("Bu adla bir yetkinlik zaten var.") from exc
    record(db, "competency.create", "competency", cp.id, {"name": [None, cp.name]})
    return _comp(cp)


def list_for_user(db: Session, user: User, user_id: UUID) -> list[c.UserCompetency]:
    target = get_visible_user(db, user, user_id)
    rows = db.scalars(select(UserCompetency).where(UserCompetency.user_id == target.id)).unique()
    return sorted((_uc(r) for r in rows), key=lambda x: (-x.level, x.competency.name))


def upsert(
    db: Session, user: User, user_id: UUID, competency_id: UUID, body: c.UserCompetencyUpsert
) -> c.UserCompetency:
    target = get_visible_user(db, user, user_id)
    cp = db.get(Competency, competency_id)
    if cp is None:
        raise NotFound("Yetkinlik bulunamadı.")
    is_self = target.id == user.id
    can_verify = P.can_verify_competency(db, user, target)
    P.require(
        not P.is_read_only(user) and (is_self or can_verify), user, "user_competency.upsert", str(target.id)
    )
    if body.verified is not None:
        P.require(can_verify, user, "user_competency.verify", str(target.id))
    uc = db.get(UserCompetency, (target.id, cp.id))
    before = (uc.level, uc.evidence) if uc else (None, None)
    if uc is None:
        uc = UserCompetency(user_id=target.id, competency_id=cp.id, level=body.level)
        db.add(uc)
    uc.level, uc.evidence = body.level, body.evidence
    if is_self and before != (uc.level, uc.evidence):  # kendi değişikliği doğrulamayı sıfırlar
        uc.verified_by, uc.verified_at = None, None
    if body.verified is True:
        uc.verified_by, uc.verified_at = user.id, utcnow()
        record(db, "user_competency.verify", "user", target.id, {"competency": [None, cp.name]})
    elif body.verified is False:
        uc.verified_by, uc.verified_at = None, None
    record(
        db,
        "user_competency.upsert",
        "user",
        target.id,
        {"competency": [None, cp.name], "level": [before[0], uc.level]},
    )
    db.flush()
    db.refresh(uc)
    return _uc(uc)


def remove(db: Session, user: User, user_id: UUID, competency_id: UUID) -> None:
    target = get_visible_user(db, user, user_id)
    P.require(
        not P.is_read_only(user) and (target.id == user.id or P.can_verify_competency(db, user, target)),
        user,
        "user_competency.delete",
        str(target.id),
    )
    uc = db.get(UserCompetency, (target.id, competency_id))
    if uc is None:
        raise NotFound("Kayıt bulunamadı.")
    db.delete(uc)
    record(db, "user_competency.delete", "user", target.id, {"competencyId": [str(competency_id), None]})


def matrix(db: Session, user: User, team_id: UUID) -> c.CompetencyMatrix:
    team = db.get(Team, team_id)
    if team is None or not in_scope(team_id, visible_team_ids(db, user)):
        raise NotFound("Ekip bulunamadı.")
    P.require(P.can_read_team_matrix(db, user, team_id), user, "competency.matrix", str(team_id))
    members = list(
        db.scalars(
            select(User).where(User.team_id == team_id, User.is_active.is_(True)).order_by(User.full_name)
        ).unique()
    )
    levels: dict[UUID, dict[str, int]] = {m.id: {} for m in members}
    used: set[UUID] = set()
    for uc in db.scalars(select(UserCompetency).where(UserCompetency.user_id.in_(levels))).unique():
        levels[uc.user_id][str(uc.competency_id)] = uc.level
        used.add(uc.competency_id)
    comps = [x for x in catalog(db) if x.id in used]
    return c.CompetencyMatrix(
        team_id=team_id,
        competencies=comps,
        members=[c.Member(user=user_ref(m), levels=levels[m.id]) for m in members],
    )
