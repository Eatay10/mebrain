"""Projeler, task'lar ve yorumlar."""

import uuid
from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.contract import ProjectStatus, Recurrence, TaskCategory, TaskPriority, TaskStatus, TaskType
from app.models.base import Base, created_at_col, enum_col, updated_at_col, uuid_pk
from app.models.org import Team, User


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (UniqueConstraint("team_id", "name", name="uq_projects_team_name"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"), index=True)
    name: Mapped[str] = mapped_column(String(150))
    description: Mapped[str | None] = mapped_column(Text)
    owner_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    status: Mapped[ProjectStatus] = mapped_column(
        enum_col(ProjectStatus, "project_status"), default=ProjectStatus.ACTIVE
    )
    start_date: Mapped[date | None] = mapped_column(Date)
    due_date: Mapped[date | None] = mapped_column(Date)
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = created_at_col()
    updated_at: Mapped[datetime] = updated_at_col()
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    team: Mapped[Team] = relationship(lazy="joined")
    owner: Mapped[User | None] = relationship(foreign_keys=[owner_id], lazy="joined")


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint(
            "(type = 'PROJECT' AND project_id IS NOT NULL) OR (type = 'STANDARD' AND project_id IS NULL)",
            name="type_project",
        ),
        CheckConstraint(
            "backup_assignee_id IS NULL OR backup_assignee_id <> assignee_id", name="backup_differs"
        ),
        UniqueConstraint("recurrence_parent_id", "occurrence_date", name="uq_tasks_occurrence"),
        Index("ix_tasks_team_status_live", "team_id", "status", postgresql_where=text("deleted_at IS NULL")),
        Index("ix_tasks_assignee_status", "assignee_id", "status"),
        Index("ix_tasks_due_open", "due_date", postgresql_where=text("status <> 'DONE'")),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    type: Mapped[TaskType] = mapped_column(enum_col(TaskType, "task_type"))
    project_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("projects.id"), index=True)
    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"))
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[TaskStatus] = mapped_column(enum_col(TaskStatus, "task_status"), default=TaskStatus.TODO)
    blocked_reason: Mapped[str | None] = mapped_column(String(500))
    priority: Mapped[TaskPriority] = mapped_column(
        enum_col(TaskPriority, "task_priority"), default=TaskPriority.MEDIUM
    )
    category: Mapped[TaskCategory] = mapped_column(
        enum_col(TaskCategory, "task_category"), default=TaskCategory.OTHER
    )
    assignee_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    backup_assignee_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    due_date: Mapped[date | None] = mapped_column(Date)
    recurrence: Mapped[Recurrence] = mapped_column(
        enum_col(Recurrence, "recurrence"), default=Recurrence.NONE
    )
    recurrence_parent_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("tasks.id"))
    occurrence_date: Mapped[date | None] = mapped_column(Date)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    version: Mapped[int] = mapped_column(default=1)
    created_at: Mapped[datetime] = created_at_col()
    updated_at: Mapped[datetime] = updated_at_col()
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    team: Mapped[Team] = relationship(lazy="joined")
    project: Mapped[Project | None] = relationship(lazy="joined")
    assignee: Mapped[User | None] = relationship(foreign_keys=[assignee_id], lazy="joined")
    backup_assignee: Mapped[User | None] = relationship(foreign_keys=[backup_assignee_id], lazy="joined")
    creator: Mapped[User | None] = relationship(foreign_keys=[created_by], lazy="joined")


class TaskComment(Base):
    __tablename__ = "task_comments"

    id: Mapped[uuid.UUID] = uuid_pk()
    task_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tasks.id"), index=True)
    author_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = created_at_col()
    edited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    author: Mapped[User] = relationship(lazy="joined")
