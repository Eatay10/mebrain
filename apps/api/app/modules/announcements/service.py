"""Duyurular: yönetici → yönettiği ekip, direktör → kurum (COM-01)."""

from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app import contract as c
from app.audit.service import record
from app.auth import policies as P
from app.auth.scope import in_scope, team_filter, visible_team_ids
from app.contract import NotificationType as NT
from app.contract import Role
from app.core.errors import BadRequest, NotFound
from app.core.schemas import PageParams, user_ref
from app.models import Announcement, User
from app.models.base import utcnow
from app.modules.notifications.service import notify


def to_contract(a: Announcement) -> c.Announcement:
    return c.Announcement(
        id=a.id,
        scope=a.scope,
        team_id=a.team_id,
        title=a.title,
        body=a.body,
        author=user_ref(a.author),
        pinned=a.pinned,
        created_at=a.created_at,
    )


def list_for(db: Session, user: User, pp: PageParams) -> c.AnnouncementPage:
    q = select(Announcement).where(
        Announcement.deleted_at.is_(None),
        or_(
            Announcement.scope == "ORGANIZATION",
            team_filter(Announcement.team_id, visible_team_ids(db, user)),
        ),
    )
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    rows = db.scalars(
        q.order_by(Announcement.pinned.desc(), Announcement.created_at.desc())
        .offset(pp.offset)
        .limit(pp.page_size)
    ).unique()
    return c.AnnouncementPage(
        items=[to_contract(a) for a in rows], total=total, page=pp.page, page_size=pp.page_size
    )


def create(db: Session, user: User, body: c.AnnouncementCreate) -> c.Announcement:
    scope = body.scope.value if hasattr(body.scope, "value") else str(body.scope)
    team_id = body.team_id if scope == "TEAM" else None
    if scope == "TEAM":
        if team_id is None:
            raise BadRequest(errors=[{"field": "teamId", "message": "Ekip duyurusu için zorunlu."}])
        if not in_scope(team_id, visible_team_ids(db, user)):
            raise NotFound("Ekip bulunamadı.")
    P.require(P.can_announce(db, user, scope, team_id), user, "announcement.create")
    a = Announcement(
        scope=scope,
        team_id=team_id,
        title=body.title.strip(),
        body=body.body,
        author_id=user.id,
        pinned=bool(body.pinned),
    )
    db.add(a)
    db.flush()
    record(db, "announcement.create", "announcement", a.id, {"scope": [None, scope]})
    rq = select(User.id).where(User.is_active.is_(True))
    if team_id:
        rq = rq.where(User.team_id == team_id)
    notify(
        db,
        db.scalars(rq),
        NT.ANNOUNCEMENT,
        f"Duyuru: {a.title}",
        body=a.body[:300],
        entity_type="announcement",
        entity_id=a.id,
        actor_id=user.id,
        email=False,
    )
    db.refresh(a)
    return to_contract(a)


def delete(db: Session, user: User, announcement_id: UUID) -> None:
    a = db.get(Announcement, announcement_id)
    if a is None or a.deleted_at is not None:
        raise NotFound("Duyuru bulunamadı.")
    if a.scope == "TEAM" and not in_scope(a.team_id, visible_team_ids(db, user)):
        raise NotFound("Duyuru bulunamadı.")
    P.require(
        not P.is_read_only(user) and (a.author_id == user.id or user.role == Role.DIRECTOR),
        user,
        "announcement.delete",
        str(a.id),
    )
    a.deleted_at = utcnow()
    record(db, "announcement.delete", "announcement", a.id)
