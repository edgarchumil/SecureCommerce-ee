"""Inventario de activos.

Revision ID: 20260903_02
Revises: 20260903_01
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260903_02"
down_revision: str | None = "20260903_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "assets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(180), nullable=False),
        sa.Column("internal_code", sa.String(80), nullable=False),
        sa.Column("asset_type", sa.String(32), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("owner", sa.String(160), nullable=True),
        sa.Column("technical_owner", sa.String(160), nullable=True),
        sa.Column("location", sa.String(180), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("operating_system", sa.String(120), nullable=True),
        sa.Column("manufacturer", sa.String(120), nullable=True),
        sa.Column("model", sa.String(120), nullable=True),
        sa.Column("exposure_level", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("acquisition_date", sa.Date(), nullable=True),
        sa.Column("confidentiality_criticality", sa.Integer(), nullable=False),
        sa.Column("integrity_criticality", sa.Integer(), nullable=False),
        sa.Column("availability_criticality", sa.Integer(), nullable=False),
        sa.Column("overall_criticality", sa.Integer(), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "confidentiality_criticality BETWEEN 1 AND 5", name="asset_confidentiality"
        ),
        sa.CheckConstraint("integrity_criticality BETWEEN 1 AND 5", name="asset_integrity"),
        sa.CheckConstraint("availability_criticality BETWEEN 1 AND 5", name="asset_availability"),
        sa.CheckConstraint("overall_criticality BETWEEN 1 AND 5", name="asset_overall"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "internal_code", name="uq_assets_org_code"),
    )
    op.create_index("ix_assets_organization_id", "assets", ["organization_id"])
    op.create_index(
        "ix_assets_org_type_status", "assets", ["organization_id", "asset_type", "status"]
    )
    op.create_index(
        "ix_assets_org_criticality", "assets", ["organization_id", "overall_criticality"]
    )
    op.create_table(
        "asset_dependencies",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column(
            "asset_id", sa.Uuid(), sa.ForeignKey("assets.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "depends_on_asset_id",
            sa.Uuid(),
            sa.ForeignKey("assets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("asset_id <> depends_on_asset_id", name="asset_dependency_not_self"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("asset_id", "depends_on_asset_id", name="uq_asset_dependency_pair"),
    )
    op.create_index(
        "ix_asset_dependencies_organization_id", "asset_dependencies", ["organization_id"]
    )
    op.create_index("ix_asset_dependencies_asset_id", "asset_dependencies", ["asset_id"])
    op.create_index(
        "ix_asset_dependencies_depends_on_asset_id", "asset_dependencies", ["depends_on_asset_id"]
    )
    op.execute("ALTER TABLE assets ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE asset_dependencies ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    op.drop_table("asset_dependencies")
    op.drop_table("assets")
