"""Yetkinlik kataloğu, kişisel seviye/puanlar, sertifikalar ve ekip matrisi (CMP-01..04).

Yetkinlik puanı (0–100): seviye 1–5'ten bağımsız, ölçülebilir ilerleme. Etkinlik tamamlanınca (ATTENDED) ve
sertifika eklenince ilgili yetkinliklere puan eklenir (en fazla 100). Her kaynak aynı yetkinliğe bir kez puan
verir (competency_score_logs).
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import contract as c
from app.audit.service import record
from app.auth import policies as P
from app.auth.scope import in_scope, visible_team_ids
from app.contract import CompetencyCategory as CC
from app.contract import NotificationType as NT
from app.contract import TaskCategory as TC
from app.core.errors import BadRequest, Conflict, NotFound
from app.core.schemas import user_ref
from app.models import Certification, Competency, CompetencyScoreLog, Team, User, UserCompetency
from app.models.base import utcnow
from app.modules.users.service import get_visible as get_visible_user


def _comp(cp: Competency) -> c.Competency:
    return c.Competency(id=cp.id, name=cp.name, category=cp.category, description=cp.description)


def _uc(uc: UserCompetency) -> c.UserCompetency:
    return c.UserCompetency(
        user_id=uc.user_id,
        competency=_comp(uc.competency),
        level=uc.level,
        score=uc.score,
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
    return sorted((_uc(r) for r in rows), key=lambda x: (-x.score, -x.level, x.competency.name))


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
        uc = UserCompetency(user_id=target.id, competency_id=cp.id, level=body.level, score=body.level * 20)
        db.add(uc)
    uc.level, uc.evidence = body.level, body.evidence
    if body.score is not None:
        P.require(can_verify, user, "user_competency.score", str(target.id))  # puanı yönetici belirler
        uc.score = body.score
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
    scores: dict[UUID, dict[str, int]] = {m.id: {} for m in members}
    used: set[UUID] = set()
    for uc in db.scalars(select(UserCompetency).where(UserCompetency.user_id.in_(levels))).unique():
        levels[uc.user_id][str(uc.competency_id)] = uc.level
        scores[uc.user_id][str(uc.competency_id)] = uc.score
        used.add(uc.competency_id)
    comps = [x for x in catalog(db) if x.id in used]
    return c.CompetencyMatrix(
        team_id=team_id,
        competencies=comps,
        members=[c.Member(user=user_ref(m), levels=levels[m.id], scores=scores[m.id]) for m in members],
    )


# ------------------------------------------------------------------ puan artışı
def _level_for(score: int) -> int:
    return max(1, min(5, (score + 19) // 20))


def award(
    db: Session, user_id: UUID, gains: list[tuple[UUID, int]], source_type: str, source_id: UUID, reason: str
) -> list[tuple[str, int, int]]:
    """Puanları ekler; aynı kaynak tekrar puan vermez. Dönen: (yetkinlik, önceki, yeni)."""
    changed: list[tuple[str, int, int]] = []
    for competency_id, points in gains:
        inserted = db.execute(
            insert(CompetencyScoreLog)
            .values(
                user_id=user_id,
                competency_id=competency_id,
                source_type=source_type,
                source_id=source_id,
                points=points,
                created_at=utcnow(),
            )
            .on_conflict_do_nothing(constraint="uq_score_log_source")
            .returning(CompetencyScoreLog.id)
        ).first()
        if inserted is None:
            continue
        uc = db.get(UserCompetency, (user_id, competency_id))
        if uc is None:
            uc = UserCompetency(user_id=user_id, competency_id=competency_id, level=1, score=0)
            db.add(uc)
            db.flush()
        before = uc.score
        uc.score = min(100, before + points)
        uc.level = max(uc.level, _level_for(uc.score))
        changed.append((uc.competency.name if uc.competency else str(competency_id), before, uc.score))
    if changed:
        from app.modules.notifications.service import notify

        summary = ", ".join(f"{n}: %{a} → %{b}" for n, a, b in changed)
        notify(
            db,
            [user_id],
            NT.COMPETENCY_UPDATED,
            f"Yetkinlik puanınız arttı ({reason})",
            body=summary,
            entity_type="user",
            entity_id=user_id,
        )
        record(db, "competency.award", "user", user_id, {"source": [None, f"{source_type}:{source_id}"]})
    return changed


# ------------------------------------------------------------------ sertifikalar
def _cert(db: Session, cert: Certification) -> c.Certification:
    logs = db.scalars(
        select(CompetencyScoreLog).where(
            CompetencyScoreLog.source_type == "CERTIFICATION", CompetencyScoreLog.source_id == cert.id
        )
    ).unique()
    return c.Certification(
        id=cert.id,
        user_id=cert.user_id,
        name=cert.name,
        issuer=cert.issuer,
        issued_on=cert.issued_on,
        expires_on=cert.expires_on,
        credential_url=cert.credential_url,
        competencies=[
            c.CompetencyGain(competency_id=lg.competency_id, name=lg.competency.name, points=lg.points)
            for lg in logs
        ],
        created_at=cert.created_at,
    )


def list_certifications(db: Session, user: User, user_id: UUID) -> list[c.Certification]:
    target = get_visible_user(db, user, user_id)
    rows = db.scalars(
        select(Certification)
        .where(Certification.user_id == target.id, Certification.deleted_at.is_(None))
        .order_by(Certification.issued_on.desc())
    )
    return [_cert(db, x) for x in rows]


def add_certification(db: Session, user: User, user_id: UUID, body: c.CertificationCreate) -> c.Certification:
    target = get_visible_user(db, user, user_id)
    P.require(P.can_add_certification(db, user, target), user, "certification.create", str(target.id))
    if body.expires_on and body.expires_on < body.issued_on:
        raise BadRequest(
            errors=[{"field": "expiresOn", "message": "Geçerlilik tarihi veriliş tarihinden önce olamaz."}]
        )
    url = str(body.credential_url) if body.credential_url else None
    if url and not url.lower().startswith("https://"):
        raise BadRequest(errors=[{"field": "credentialUrl", "message": "Sadece https:// bağlantıları."}])
    comp_ids = list(dict.fromkeys(body.competency_ids or []))
    found = set(db.scalars(select(Competency.id).where(Competency.id.in_(comp_ids)))) if comp_ids else set()
    if len(found) != len(comp_ids):
        raise BadRequest(errors=[{"field": "competencyIds", "message": "Bilinmeyen yetkinlik."}])
    cert = Certification(
        user_id=target.id,
        name=body.name.strip(),
        issuer=body.issuer,
        issued_on=body.issued_on,
        expires_on=body.expires_on,
        credential_url=url,
        created_by=user.id,
    )
    db.add(cert)
    db.flush()
    record(db, "certification.create", "user", target.id, {"certification": [None, cert.name]})
    award(db, target.id, [(cid, body.points or 15) for cid in comp_ids], "CERTIFICATION", cert.id, cert.name)
    db.flush()
    return _cert(db, cert)


def delete_certification(db: Session, user: User, certification_id: UUID) -> None:
    cert = db.get(Certification, certification_id)
    if cert is None or cert.deleted_at is not None:
        raise NotFound("Sertifika bulunamadı.")
    target = get_visible_user(db, user, cert.user_id)
    P.require(P.can_add_certification(db, user, target), user, "certification.delete", str(target.id))
    cert.deleted_at = utcnow()
    record(db, "certification.delete", "user", target.id, {"certification": [cert.name, None]})


# ------------------------------------------------------------------ atama önerisi
CATEGORY_MAP: dict[TC, tuple[CC, ...]] = {
    TC.INCIDENT_RESPONSE: (CC.FORENSICS, CC.DEFENSIVE),
    TC.VULNERABILITY_MANAGEMENT: (CC.APPSEC, CC.OFFENSIVE, CC.DEFENSIVE),
    TC.MONITORING: (CC.DEFENSIVE, CC.NETWORK),
    TC.PENETRATION_TEST: (CC.OFFENSIVE, CC.APPSEC),
    TC.COMPLIANCE: (CC.GRC,),
    TC.THREAT_INTEL: (CC.DEFENSIVE, CC.FORENSICS),
    TC.AWARENESS: (CC.GRC,),
    TC.OPERATIONS: (CC.NETWORK, CC.CLOUD),
}


def scores_for_category(
    db: Session, user_ids: list[UUID], category: TC
) -> dict[UUID, tuple[int, list[c.Competency1]]]:
    """Kişi başına ilgili alanlardaki en iyi 3 yetkinliğin ortalama puanı ve ayrıntısı."""
    cats = CATEGORY_MAP.get(category)
    q = (
        select(UserCompetency)
        .join(Competency, Competency.id == UserCompetency.competency_id)
        .where(UserCompetency.user_id.in_(user_ids))
    )
    if cats:
        q = q.where(Competency.category.in_(cats))
    per: dict[UUID, list[UserCompetency]] = {}
    for uc in db.scalars(q).unique():
        per.setdefault(uc.user_id, []).append(uc)
    out: dict[UUID, tuple[int, list[c.Competency1]]] = {}
    for uid, rows in per.items():
        top = sorted(rows, key=lambda r: -r.score)[:3]
        avg = round(sum(r.score for r in top) / len(top)) if top else 0
        out[uid] = (avg, [c.Competency1(name=r.competency.name, score=r.score) for r in top])
    return out
