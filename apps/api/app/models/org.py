"""Organizasyon: unit'ler, ekipler ve kullanıcılar."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import CITEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.contract import Role
from app.models.base import Base, created_at_col, enum_col, updated_at_col, uuid_pk


class Unit(Base):
    """Direktör ile ekipler arasındaki katman; unit yöneticisi (UNIT_MANAGER) yönetir."""

    __tablename__ = "units"

    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    manager_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", use_alter=True, name="fk_units_manager_id_users"), index=True
    )
    created_at: Mapped[datetime] = created_at_col()
    updated_at: Mapped[datetime] = updated_at_col()

    manager: Mapped["User | None"] = relationship(foreign_keys=[manager_id], lazy="joined")


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    manager_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", use_alter=True, name="fk_teams_manager_id_users"), index=True
    )
    unit_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("units.id"), index=True)
    created_at: Mapped[datetime] = created_at_col()
    updated_at: Mapped[datetime] = updated_at_col()

    manager: Mapped["User | None"] = relationship(foreign_keys=[manager_id], lazy="joined")
    unit: Mapped[Unit | None] = relationship(foreign_keys=[unit_id], lazy="joined")


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = uuid_pk()
    email: Mapped[str] = mapped_column(CITEXT, unique=True)
    full_name: Mapped[str] = mapped_column(String(120))
    title: Mapped[str | None] = mapped_column(String(120))
    role: Mapped[Role] = mapped_column(enum_col(Role, "role"))
    team_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("teams.id"), index=True)
    password_hash: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(default=True)
    failed_login_count: Mapped[int] = mapped_column(default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = created_at_col()
    updated_at: Mapped[datetime] = updated_at_col()

    team: Mapped[Team | None] = relationship(foreign_keys=[team_id], lazy="joined")
