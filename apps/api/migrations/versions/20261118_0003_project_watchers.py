"""project watchers (stars)

Revision ID: 0003
Revises: 0002
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "project_watchers",
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name=op.f("fk_project_watchers_project_id_projects"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_project_watchers_user_id_users")),
        sa.PrimaryKeyConstraint("project_id", "user_id", name=op.f("pk_project_watchers")),
    )
    op.create_index(op.f("ix_project_watchers_user_id"), "project_watchers", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_project_watchers_user_id"), table_name="project_watchers")
    op.drop_table("project_watchers")
