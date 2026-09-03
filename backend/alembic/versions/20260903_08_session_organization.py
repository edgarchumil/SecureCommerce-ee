"""Persist selected organization in sessions.

Revision ID: 20260903_08
Revises: 20260903_07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260903_08"
down_revision: str | None = "20260903_07"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("sessions", sa.Column("organization_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_sessions_organization_id", "sessions", "organizations", ["organization_id"], ["id"]
    )
    op.create_index("ix_sessions_organization_id", "sessions", ["organization_id"])


def downgrade() -> None:
    op.drop_index("ix_sessions_organization_id", table_name="sessions")
    op.drop_constraint("fk_sessions_organization_id", "sessions", type_="foreignkey")
    op.drop_column("sessions", "organization_id")
