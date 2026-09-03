"""Recomendaciones asistidas por IA.

Revision ID: 20260903_05
Revises: 20260903_04
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260903_05"
down_revision: str | None = "20260903_04"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ai_recommendations",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("risk_id", sa.Uuid(), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("reviewed_by", sa.Uuid(), nullable=True),
        sa.Column("kind", sa.String(40), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("title", sa.String(220), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("actions", sa.JSON(), nullable=False),
        sa.Column("references", sa.JSON(), nullable=False),
        sa.Column("provider", sa.String(40), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("prompt_version", sa.String(30), nullable=False),
        sa.Column("is_fallback", sa.Boolean(), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False),
        sa.Column("output_tokens", sa.Integer(), nullable=False),
        sa.Column("estimated_cost_usd", sa.Float(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["risk_id"], ["risks.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ai_recommendations_organization_id", "ai_recommendations", ["organization_id"]
    )
    op.create_index(
        "ix_ai_recommendations_org_status", "ai_recommendations", ["organization_id", "status"]
    )
    op.create_index(
        "ix_ai_recommendations_org_risk", "ai_recommendations", ["organization_id", "risk_id"]
    )
    op.execute("ALTER TABLE ai_recommendations ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    op.drop_table("ai_recommendations")
