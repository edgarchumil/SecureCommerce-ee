"""Evaluaciones NIST CSF 2.0.

Revision ID: 20260903_03
Revises: 20260903_02
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260903_03"
down_revision: str | None = "20260903_02"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "frameworks",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("code", sa.String(40), nullable=False),
        sa.Column("name", sa.String(180), nullable=False),
        sa.Column("version", sa.String(30), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        *timestamps(),
        sa.UniqueConstraint("code", "version", name="uq_framework_code_version"),
    )
    op.create_table(
        "framework_functions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("framework_id", sa.Uuid(), sa.ForeignKey("frameworks.id"), nullable=False),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        *timestamps(),
        sa.UniqueConstraint("framework_id", "code", name="uq_function_framework_code"),
    )
    op.create_table(
        "framework_categories",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "function_id", sa.Uuid(), sa.ForeignKey("framework_functions.id"), nullable=False
        ),
        sa.Column("code", sa.String(30), nullable=False),
        sa.Column("name", sa.String(140), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        *timestamps(),
        sa.UniqueConstraint("function_id", "code", name="uq_category_function_code"),
    )
    op.create_table(
        "framework_controls",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "category_id", sa.Uuid(), sa.ForeignKey("framework_categories.id"), nullable=False
        ),
        sa.Column("code", sa.String(40), nullable=False),
        sa.Column("title", sa.String(220), nullable=False),
        sa.Column("description", sa.Text()),
        *timestamps(),
        sa.UniqueConstraint("category_id", "code", name="uq_control_category_code"),
    )
    op.create_table(
        "questions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("control_id", sa.Uuid(), sa.ForeignKey("framework_controls.id"), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("help_text", sa.Text(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("expected_evidence", sa.Text(), nullable=False),
        sa.Column("response_options", sa.JSON(), nullable=False),
        sa.Column("base_recommendation", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        *timestamps(),
    )
    op.create_table(
        "evaluations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("framework_id", sa.Uuid(), sa.ForeignKey("frameworks.id"), nullable=False),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("name", sa.String(180), nullable=False),
        sa.Column("scope", sa.Text(), nullable=False),
        sa.Column("target_maturity", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("comments", sa.Text()),
        *timestamps(),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("target_maturity BETWEEN 0 AND 4", name="evaluation_target_maturity"),
        sa.UniqueConstraint(
            "organization_id", "code", "version", name="uq_evaluation_org_code_version"
        ),
    )
    op.create_table(
        "evaluation_assets",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column(
            "evaluation_id",
            sa.Uuid(),
            sa.ForeignKey("evaluations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("asset_id", sa.Uuid(), sa.ForeignKey("assets.id"), nullable=False),
        *timestamps(),
        sa.UniqueConstraint("evaluation_id", "asset_id", name="uq_evaluation_asset"),
    )
    op.create_table(
        "answers",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column(
            "evaluation_id",
            sa.Uuid(),
            sa.ForeignKey("evaluations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("question_id", sa.Uuid(), sa.ForeignKey("questions.id"), nullable=False),
        sa.Column("answered_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("maturity", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text()),
        *timestamps(),
        sa.CheckConstraint("maturity BETWEEN 0 AND 4", name="answer_maturity"),
        sa.UniqueConstraint("evaluation_id", "question_id", name="uq_answer_evaluation_question"),
    )
    op.create_table(
        "evidence",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column(
            "answer_id", sa.Uuid(), sa.ForeignKey("answers.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("uploaded_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("storage_key", sa.String(500), nullable=False, unique=True),
        sa.Column("sha256", sa.String(64), nullable=False),
        *timestamps(),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    for table in ("evaluations", "evaluation_assets", "answers", "evidence"):
        op.create_index(f"ix_{table}_organization_id", table, ["organization_id"])
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.create_index("ix_evaluations_org_status", "evaluations", ["organization_id", "status"])
    op.create_index("ix_answers_org_evaluation", "answers", ["organization_id", "evaluation_id"])


def downgrade() -> None:
    for table in (
        "evidence",
        "answers",
        "evaluation_assets",
        "evaluations",
        "questions",
        "framework_controls",
        "framework_categories",
        "framework_functions",
        "frameworks",
    ):
        op.drop_table(table)
