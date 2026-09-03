"""Gestión de riesgos.

Revision ID: 20260903_04
Revises: 20260903_03
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260903_04"
down_revision: str | None = "20260903_03"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def common() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    ]


def upgrade() -> None:
    for table in ("threats", "vulnerabilities"):
        rating = "likelihood" if table == "threats" else "severity"
        op.create_table(
            table,
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column(
                "organization_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False
            ),
            sa.Column("created_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("name", sa.String(180), nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column(rating, sa.Integer(), nullable=False),
            *common(),
            sa.CheckConstraint(f"{rating} BETWEEN 1 AND 5", name=f"{table}_{rating}"),
        )
        op.create_index(f"ix_{table}_organization_id", table, ["organization_id"])
        op.create_index(f"ix_{table}_org_name", table, ["organization_id", "name"])
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.create_table(
        "risks",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("asset_id", sa.Uuid(), sa.ForeignKey("assets.id"), nullable=False),
        sa.Column("threat_id", sa.Uuid(), sa.ForeignKey("threats.id")),
        sa.Column("vulnerability_id", sa.Uuid(), sa.ForeignKey("vulnerabilities.id")),
        sa.Column("probability", sa.Integer(), nullable=False),
        sa.Column("impact", sa.Integer(), nullable=False),
        sa.Column("inherent_score", sa.Integer(), nullable=False),
        sa.Column("inherent_level", sa.String(20), nullable=False),
        sa.Column("existing_controls", sa.Text()),
        sa.Column("residual_probability", sa.Integer(), nullable=False),
        sa.Column("residual_impact", sa.Integer(), nullable=False),
        sa.Column("residual_score", sa.Integer(), nullable=False),
        sa.Column("residual_level", sa.String(20), nullable=False),
        sa.Column("treatment_strategy", sa.String(20), nullable=False),
        sa.Column("responsible_user_id", sa.Uuid(), sa.ForeignKey("users.id")),
        sa.Column("target_date", sa.Date()),
        sa.Column("progress", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        *common(),
        sa.CheckConstraint("probability BETWEEN 1 AND 5", name="risk_probability"),
        sa.CheckConstraint("impact BETWEEN 1 AND 5", name="risk_impact"),
        sa.CheckConstraint(
            "residual_probability BETWEEN 1 AND 5", name="risk_residual_probability"
        ),
        sa.CheckConstraint("residual_impact BETWEEN 1 AND 5", name="risk_residual_impact"),
        sa.CheckConstraint("progress BETWEEN 0 AND 100", name="risk_progress"),
        sa.UniqueConstraint("organization_id", "code", name="uq_risks_org_code"),
    )
    op.create_index("ix_risks_organization_id", "risks", ["organization_id"])
    op.create_index(
        "ix_risks_org_level_status", "risks", ["organization_id", "inherent_level", "status"]
    )
    op.create_index("ix_risks_org_target", "risks", ["organization_id", "target_date"])
    op.create_table(
        "risk_treatments",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column(
            "risk_id", sa.Uuid(), sa.ForeignKey("risks.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("responsible_user_id", sa.Uuid(), sa.ForeignKey("users.id")),
        sa.Column("target_date", sa.Date()),
        sa.Column("progress", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text()),
        *common(),
        sa.CheckConstraint("progress BETWEEN 0 AND 100", name="treatment_progress"),
    )
    op.create_index("ix_treatments_org_risk", "risk_treatments", ["organization_id", "risk_id"])
    op.create_table(
        "system_settings",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id")),
        sa.Column("key", sa.String(100), nullable=False),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.Column("updated_by", sa.Uuid(), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id", "key", name="uq_settings_org_key"),
    )
    for table in ("risks", "risk_treatments", "system_settings"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    for table in ("risk_treatments", "risks", "system_settings", "vulnerabilities", "threats"):
        op.drop_table(table)
