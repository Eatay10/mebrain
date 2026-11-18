"""Bildirim üretimi ve okuma. Aktör kendi işlemi için bildirim almaz (NTF-01-a)."""

import uuid
from collections.abc import Iterable
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app import contract as c
from app.core.errors import NotFound
from app.core.schemas import PageParams
from app.models import Notification, User
from app.models.base import utcnow


def notify(
    db: Session,
    recipients: Iterable[UUID | None],
    ntype: c.NotificationType,
    title: str,
    body: str | None = None,
    entity_type: str | None = None,
    entity_id: UUID | None = None,
    actor_id: UUID | None = None,
    dedup_key: str | None = None,
    email: bool = True,
) -> int:
    ids = {r for r in recipients if r is not None and r != actor_id}
    if not ids:
        return 0
    active = set(db.scalars(select(User.id).where(User.id.in_(ids), User.is_active.is_(True))))
    rows = [
        {
            "id": uuid.uuid4(),
            "user_id": uid,
            "type": ntype.value,
            "title": title[:200],
            "body": (body or "")[:1000] or None,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "email_status": "PENDING" if email else "NONE",
            "dedup_key": f"{dedup_key}:{uid}" if dedup_key else None,
            "created_at": utcnow(),
        }
        for uid in active
    ]
    if not rows:
        return 0
    stmt = insert(Notification).values(rows).on_conflict_do_nothing(index_elements=["dedup_key"])
    return len(db.execute(stmt.returning(Notification.id)).all())


def to_contract(n: Notification) -> c.Notification:
    return c.Notification(
        id=n.id,
        type=n.type,
        title=n.title,
        body=n.body,
        entity_type=n.entity_type,
        entity_id=n.entity_id,
        read_at=n.read_at,
        created_at=n.created_at,
    )


def list_for(db: Session, user: User, pp: PageParams, unread: bool | None) -> c.NotificationPage:
    q = select(Notification).where(Notification.user_id == user.id)
    if unread is True:
        q = q.where(Notification.read_at.is_(None))
    elif unread is False:
        q = q.where(Notification.read_at.is_not(None))
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    items = db.scalars(q.order_by(Notification.created_at.desc()).offset(pp.offset).limit(pp.page_size))
    return c.NotificationPage(
        items=[to_contract(n) for n in items], total=total, page=pp.page, page_size=pp.page_size
    )


def unread_count(db: Session, user: User) -> int:
    return (
        db.scalar(select(func.count()).where(Notification.user_id == user.id, Notification.read_at.is_(None)))
        or 0
    )


def mark_read(db: Session, user: User, notification_id: UUID) -> None:
    n = db.get(Notification, notification_id)
    if n is None or n.user_id != user.id:
        raise NotFound("Bildirim bulunamadı.")
    n.read_at = n.read_at or utcnow()


def mark_all_read(db: Session, user: User) -> None:
    db.execute(
        update(Notification)
        .where(Notification.user_id == user.id, Notification.read_at.is_(None))
        .values(read_at=utcnow())
    )
