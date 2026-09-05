"""Preserve generated PDFs across service restarts."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260905_09"
down_revision: str | None = "20260903_08"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("reports", sa.Column("pdf_content", sa.LargeBinary(), nullable=True))


def downgrade() -> None:
    op.drop_column("reports", "pdf_content")
