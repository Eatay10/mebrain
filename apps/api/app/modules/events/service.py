"""Etkinlikler ve katılımlar (EVT-01..03). Etkinlikler kurum genelinde görünür; katılımlar kapsamla."""

from datetime import date, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app import contract as c
from app.audit.service import diff, record
from app.auth import policies as P
from app.auth.scope import team_filter, visible_team_ids
from app.contract import NotificationType as NT
from app.contract import ParticipationStatus as PS
from app.core.errors import BadRequest, Conflict, InvalidTransition, NotFound
from app.core.schemas import PageParams, user_ref
from app.models import Event, EventParticipation, User
from app.models.base import utcnow
from app.modules.notifications.service import notify
from app.modules.tasks.repository import escape_like

ACTIVE = (PS.REQUESTED, PS.APPROVED, PS.ATTENDED)
DECISIONS = {
    PS.REQUESTED: {PS.APPROVED, PS.REJECTED, PS.CANCELLED},
    PS.APPROVED: {PS.ATTENDED, PS.CANCELLED},
}
TRACKED = ("title", "type", "description", "organizer", "location", "url", "starts_at", "ends_at")
STATUS_TR = {
    PS.APPROVED: "onaylandı",
    PS.REJECTED: "reddedildi",
    PS.ATTENDED: "katıldı olarak işaretlendi",
    PS.CANCELLED: "iptal edildi",
}


def _url(value: Any) -> str | None:
    if value is None:
        return None
    s = str(value)
    if not s.lower().startswith("https://") or len(s) > 500:
        raise BadRequest(
            errors=[{"field": "url", "message": "Sadece https:// bağlantıları (en fazla 500 karakter)."}]
        )
    return s


def _participation(p: EventParticipation) -> c.Participation:
    return c.Participation(
        id=p.id,
        event_id=p.event_id,
        user=user_ref(p.user),
        role=p.role,
        status=p.status,
        decided_by=user_ref(p.decider),
        decided_at=p.decided_at,
        note=p.note,
        created_at=p.created_at,
    )


def _to_contract(e: Event, count: int, mine: EventParticipation | None) -> c.Event:
    return c.Event(
        id=e.id,
        title=e.title,
        type=e.type,
        scope=e.scope,
        description=e.description,
        organizer=e.organizer,
        location=e.location,
        url=e.url,
        starts_at=e.starts_at,
        ends_at=e.ends_at,
        created_by=user_ref(e.creator),
        participant_count=count,
        my_participation=_participation(mine) if mine else None,
    )


def _enrich(db: Session, user: User, events: list[Event]) -> list[c.Event]:
    ids = [e.id for e in events]
    counts = (
        dict(
            db.execute(
                select(EventParticipation.event_id, func.count())
                .where(EventParticipation.event_id.in_(ids), EventParticipation.status.in_(ACTIVE))
                .group_by(EventParticipation.event_id)
            ).all()
        )
        if ids
        else {}
    )
    mine = (
        {
            p.event_id: p
            for p in db.scalars(
                select(EventParticipation).where(
                    EventParticipation.event_id.in_(ids), EventParticipation.user_id == user.id
                )
            ).unique()
        }
        if ids
        else {}
    )
    return [_to_contract(e, counts.get(e.id, 0), mine.get(e.id)) for e in events]


def get_event(db: Session, event_id: UUID) -> Event:
    e = db.get(Event, event_id)
    if e is None or e.deleted_at is not None:
        raise NotFound("Etkinlik bulunamadı.")
    return e


def list_events(
    db: Session,
    user: User,
    pp: PageParams,
    q: str | None,
    scope: c.EventScope | None,
    etype: c.EventType | None,
    frm: date | None,
    to: date | None,
    participant: str | None,
) -> c.EventPage:
    stmt = select(Event).where(Event.deleted_at.is_(None))
    if q:
        stmt = stmt.where(Event.title.ilike(f"%{escape_like(q)}%", escape="\\"))
    if scope:
        stmt = stmt.where(Event.scope == scope)
    if etype:
        stmt = stmt.where(Event.type == etype)
    if frm:
        stmt = stmt.where(Event.ends_at >= frm)
    if to:
        stmt = stmt.where(Event.starts_at < to + timedelta(days=1))
    if participant:
        try:
            pid = user.id if participant == "me" else UUID(participant)
        except ValueError as exc:
            raise BadRequest(
                errors=[{"field": "participantId", "message": "UUID veya 'me' olmalı."}]
            ) from exc
        stmt = stmt.where(
            Event.id.in_(
                select(EventParticipation.event_id).where(
                    EventParticipation.user_id == pid, EventParticipation.status.in_(ACTIVE)
                )
            )
        )
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = list(
        db.scalars(stmt.order_by(Event.starts_at.desc()).offset(pp.offset).limit(pp.page_size)).unique()
    )
    return c.EventPage(items=_enrich(db, user, rows), total=total, page=pp.page, page_size=pp.page_size)


def get(db: Session, user: User, event_id: UUID) -> c.Event:
    return _enrich(db, user, [get_event(db, event_id)])[0]


def create(db: Session, user: User, body: c.EventCreate) -> c.Event:
    P.require(P.can_create_event(user, body.scope), user, "event.create")
    if body.ends_at < body.starts_at:
        raise BadRequest(errors=[{"field": "endsAt", "message": "Bitiş başlangıçtan önce olamaz."}])
    e = Event(
        title=body.title.strip(),
        type=body.type,
        scope=body.scope,
        description=body.description,
        organizer=body.organizer,
        location=body.location,
        url=_url(body.url),
        starts_at=body.starts_at,
        ends_at=body.ends_at,
        created_by=user.id,
    )
    db.add(e)
    db.flush()
    record(db, "event.create", "event", e.id, {"title": [None, e.title], "scope": [None, e.scope.value]})
    db.refresh(e)
    return _to_contract(e, 0, None)


def update(db: Session, user: User, event_id: UUID, body: c.EventUpdate) -> c.Event:
    e = get_event(db, event_id)
    P.require(P.can_edit_event(user, e), user, "event.update", str(e.id))
    before = {k: getattr(e, k) for k in TRACKED}
    for name in body.model_fields_set:
        value = getattr(body, name)
        if name in ("title", "type", "starts_at", "ends_at") and value is None:
            raise BadRequest(errors=[{"field": name, "message": "Boş olamaz."}])
        setattr(e, name, _url(value) if name == "url" else value)
    if e.ends_at < e.starts_at:
        raise BadRequest(errors=[{"field": "endsAt", "message": "Bitiş başlangıçtan önce olamaz."}])
    changes = diff(before, {k: getattr(e, k) for k in TRACKED})
    if changes:
        record(db, "event.update", "event", e.id, changes)
    db.flush()
    return get(db, user, e.id)


def delete(db: Session, user: User, event_id: UUID) -> None:
    e = get_event(db, event_id)
    P.require(P.can_edit_event(user, e), user, "event.delete", str(e.id))
    e.deleted_at = utcnow()
    record(db, "event.delete", "event", e.id)


def list_participations(db: Session, user: User, event_id: UUID) -> list[c.Participation]:
    e = get_event(db, event_id)
    stmt = (
        select(EventParticipation)
        .join(User, EventParticipation.user_id == User.id)
        .where(
            EventParticipation.event_id == e.id,
            or_(team_filter(User.team_id, visible_team_ids(db, user)), User.id == user.id),
        )
        .order_by(EventParticipation.created_at)
    )
    return [_participation(p) for p in db.scalars(stmt).unique()]


def request(db: Session, user: User, event_id: UUID, body: c.ParticipationCreate) -> c.Participation:
    e = get_event(db, event_id)
    target = user if body.user_id in (None, user.id) else db.get(User, body.user_id)
    if target is None or not target.is_active:
        raise NotFound("Kullanıcı bulunamadı.")
    P.require(P.can_request_participation(db, user, target), user, "participation.request", str(e.id))
    p = db.scalar(
        select(EventParticipation).where(
            EventParticipation.event_id == e.id, EventParticipation.user_id == target.id
        )
    )
    if p is not None and p.status != PS.CANCELLED:
        raise Conflict("Bu etkinlik için zaten bir katılım kaydı var.")
    if p is None:
        p = EventParticipation(event_id=e.id, user_id=target.id, role=body.role, note=body.note)
        db.add(p)
    else:
        p.status, p.role, p.note, p.decided_by, p.decided_at = PS.REQUESTED, body.role, body.note, None, None
    db.flush()
    record(
        db,
        "participation.request",
        "participation",
        p.id,
        {"eventId": [None, str(e.id)], "userId": [None, str(target.id)]},
    )
    manager_id = target.team.manager_id if target.team else None
    notify(
        db,
        [manager_id],
        NT.PARTICIPATION_DECIDED,
        f"Katılım talebi: {target.full_name} — {e.title}",
        entity_type="event",
        entity_id=e.id,
        actor_id=user.id,
        email=False,
    )
    db.refresh(p)
    return _participation(p)


def decide(db: Session, user: User, participation_id: UUID, body: c.ParticipationDecision) -> c.Participation:
    p = db.get(EventParticipation, participation_id)
    if p is None or (p.user_id != user.id and not P.can_read_user(db, user, p.user)):
        raise NotFound("Katılım kaydı bulunamadı.")
    to = PS(body.status.value)
    if to not in DECISIONS.get(p.status, set()):
        raise InvalidTransition(f"{p.status.value} → {to.value} geçişi geçersiz.")
    P.require(P.can_decide_participation(db, user, p, to), user, "participation.decide", str(p.id))
    frm = p.status
    p.status, p.decided_by, p.decided_at = to, user.id, utcnow()
    if body.note is not None:
        p.note = body.note
    record(db, "participation.decide", "participation", p.id, {"status": [frm.value, to.value]})
    event = db.get(Event, p.event_id)
    notify(
        db,
        [p.user_id],
        NT.PARTICIPATION_DECIDED,
        f"Katılımınız {STATUS_TR[to]}: {event.title if event else ''}",
        entity_type="event",
        entity_id=p.event_id,
        actor_id=user.id,
    )
    db.flush()
    db.refresh(p)
    return _participation(p)
