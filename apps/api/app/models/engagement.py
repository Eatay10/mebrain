"""Etkinlikler, katılımlar ve yetkinlikler."""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, SmallInteger, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.contract import CompetencyCategory, EventScope, EventType, ParticipationRole, ParticipationStatus
from app.models.base import Base, created_at_col, enum_col, updated_at_col, uuid_pk
from app.models.org import User


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (CheckConstraint("ends_at >= starts_at", name="ends_after_start"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    title: Mapped[str] = mapped_column(String(200))
    type: Mapped[EventType] = mapped_column(enum_col(EventType, "event_type"))
    scope: Mapped[EventScope] = mapped_column(enum_col(EventScope, "event_scope"))
    description: Mapped[str | None] = mapped_column(Text)
    organizer: Mapped[str | None] = mapped_column(String(150))
    location: Mapped[str | None] = mapped_column(String(200))
    url: Mapped[str | None] = mapped_column(String(500))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = created_at_col()
    updated_at: Mapped[datetime] = updated_at_col()
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    creator: Mapped[User] = relationship(lazy="joined")


class EventParticipation(Base):
    __tablename__ = "event_participations"
    __table_args__ = (UniqueConstraint("event_id", "user_id", name="uq_participation_event_user"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    event_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("events.id"), index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[ParticipationRole] = mapped_column(enum_col(ParticipationRole, "participation_role"))
    status: Mapped[ParticipationStatus] = mapped_column(
        enum_col(ParticipationStatus, "participation_status"), default=ParticipationStatus.REQUESTED
    )
    decided_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    note: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = created_at_col()

    user: Mapped[User] = relationship(foreign_keys=[user_id], lazy="joined")
    decider: Mapped[User | None] = relationship(foreign_keys=[decided_by], lazy="joined")


class Competency(Base):
    __tablename__ = "competencies"

    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(100), unique=True)
    category: Mapped[CompetencyCategory] = mapped_column(enum_col(CompetencyCategory, "competency_category"))
    description: Mapped[str | None] = mapped_column(Text)


class UserCompetency(Base):
    __tablename__ = "user_competencies"
    __table_args__ = (CheckConstraint("level BETWEEN 1 AND 5", name="level_range"),)

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    competency_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("competencies.id"), primary_key=True)
    level: Mapped[int] = mapped_column(SmallInteger)
    evidence: Mapped[str | None] = mapped_column(String(500))
    verified_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = updated_at_col()

    competency: Mapped[Competency] = relationship(lazy="joined")
    verifier: Mapped[User | None] = relationship(foreign_keys=[verified_by], lazy="joined")
