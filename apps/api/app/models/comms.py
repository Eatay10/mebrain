"""Bildirimler ve duyurular."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.contract import NotificationType, ReportFrequency
from app.models.base import Base, created_at_col, enum_col, uuid_pk
from app.models.org import User


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (Index("ix_notifications_user_unread", "user_id", "read_at"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    type: Mapped[NotificationType] = mapped_column(String(40))
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str | None] = mapped_column(String(1000))
    entity_type: Mapped[str | None] = mapped_column(String(40))
    entity_id: Mapped[uuid.UUID | None]
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    email_status: Mapped[str] = mapped_column(String(10), default="NONE")  # NONE|PENDING|SENT|FAILED
    email_attempts: Mapped[int] = mapped_column(default=0)
    dedup_key: Mapped[str | None] = mapped_column(String(200), unique=True)
    created_at: Mapped[datetime] = created_at_col()

    user: Mapped[User] = relationship(lazy="joined")


class Announcement(Base):
    __tablename__ = "announcements"

    id: Mapped[uuid.UUID] = uuid_pk()
    scope: Mapped[str] = mapped_column(String(20))  # TEAM | ORGANIZATION
    team_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("teams.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    author_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    pinned: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = created_at_col()
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    author: Mapped[User] = relationship(lazy="joined")


class ReportSchedule(Base):
    """Haftalık/aylık planlı rapor; worker sahibin yetki kapsamıyla üretip e-postalar."""

    __tablename__ = "report_schedules"

    id: Mapped[uuid.UUID] = uuid_pk()
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    frequency: Mapped[ReportFrequency] = mapped_column(enum_col(ReportFrequency, "report_frequency"))
    group_by: Mapped[str] = mapped_column(String(20))
    team_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("teams.id"))
    active: Mapped[bool] = mapped_column(default=True)
    next_run_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_status: Mapped[str | None] = mapped_column(String(10))
    created_at: Mapped[datetime] = created_at_col()

    owner: Mapped[User] = relationship(lazy="joined")
