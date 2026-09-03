from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class EvaluationStatus(StrEnum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    CLOSED = "closed"


class Framework(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "frameworks"
    __table_args__ = (UniqueConstraint("code", "version", name="uq_framework_code_version"),)

    code: Mapped[str] = mapped_column(String(40))
    name: Mapped[str] = mapped_column(String(180))
    version: Mapped[str] = mapped_column(String(30))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    functions: Mapped[list["FrameworkFunction"]] = relationship(
        back_populates="framework", cascade="all, delete-orphan"
    )


class FrameworkFunction(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "framework_functions"
    __table_args__ = (UniqueConstraint("framework_id", "code", name="uq_function_framework_code"),)

    framework_id: Mapped[UUID] = mapped_column(ForeignKey("frameworks.id"), index=True)
    code: Mapped[str] = mapped_column(String(20))
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer)
    framework: Mapped[Framework] = relationship(back_populates="functions")
    categories: Mapped[list["FrameworkCategory"]] = relationship(
        back_populates="function", cascade="all, delete-orphan"
    )


class FrameworkCategory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "framework_categories"
    __table_args__ = (UniqueConstraint("function_id", "code", name="uq_category_function_code"),)

    function_id: Mapped[UUID] = mapped_column(ForeignKey("framework_functions.id"), index=True)
    code: Mapped[str] = mapped_column(String(30))
    name: Mapped[str] = mapped_column(String(140))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer)
    function: Mapped[FrameworkFunction] = relationship(back_populates="categories")
    controls: Mapped[list["FrameworkControl"]] = relationship(
        back_populates="category", cascade="all, delete-orphan"
    )


class FrameworkControl(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "framework_controls"
    __table_args__ = (UniqueConstraint("category_id", "code", name="uq_control_category_code"),)

    category_id: Mapped[UUID] = mapped_column(ForeignKey("framework_categories.id"), index=True)
    code: Mapped[str] = mapped_column(String(40))
    title: Mapped[str] = mapped_column(String(220))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[FrameworkCategory] = relationship(back_populates="controls")
    questions: Mapped[list["Question"]] = relationship(
        back_populates="control", cascade="all, delete-orphan"
    )


class Question(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "questions"
    __table_args__ = (Index("ix_questions_control_active", "control_id", "is_active"),)

    control_id: Mapped[UUID] = mapped_column(ForeignKey("framework_controls.id"), index=True)
    text: Mapped[str] = mapped_column(Text)
    help_text: Mapped[str] = mapped_column(Text)
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    expected_evidence: Mapped[str] = mapped_column(Text)
    response_options: Mapped[list[dict[str, object]]] = mapped_column(JSON)
    base_recommendation: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer)
    control: Mapped[FrameworkControl] = relationship(back_populates="questions")


class Evaluation(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "evaluations"
    __table_args__ = (
        Index("ix_evaluations_org_status", "organization_id", "status"),
        UniqueConstraint(
            "organization_id", "code", "version", name="uq_evaluation_org_code_version"
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    framework_id: Mapped[UUID] = mapped_column(ForeignKey("frameworks.id"), index=True)
    code: Mapped[str] = mapped_column(String(80))
    name: Mapped[str] = mapped_column(String(180))
    scope: Mapped[str] = mapped_column(Text)
    target_maturity: Mapped[int] = mapped_column(Integer, default=3)
    status: Mapped[EvaluationStatus] = mapped_column(String(20), default=EvaluationStatus.DRAFT)
    version: Mapped[int] = mapped_column(Integer, default=1)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    assets: Mapped[list["EvaluationAsset"]] = relationship(cascade="all, delete-orphan")
    answers: Mapped[list["Answer"]] = relationship(cascade="all, delete-orphan")


class EvaluationAsset(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "evaluation_assets"
    __table_args__ = (UniqueConstraint("evaluation_id", "asset_id", name="uq_evaluation_asset"),)

    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    evaluation_id: Mapped[UUID] = mapped_column(
        ForeignKey("evaluations.id", ondelete="CASCADE"), index=True
    )
    asset_id: Mapped[UUID] = mapped_column(ForeignKey("assets.id"), index=True)


class Answer(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "answers"
    __table_args__ = (
        UniqueConstraint("evaluation_id", "question_id", name="uq_answer_evaluation_question"),
        Index("ix_answers_org_evaluation", "organization_id", "evaluation_id"),
    )

    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    evaluation_id: Mapped[UUID] = mapped_column(
        ForeignKey("evaluations.id", ondelete="CASCADE"), index=True
    )
    question_id: Mapped[UUID] = mapped_column(ForeignKey("questions.id"), index=True)
    answered_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    maturity: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)


class Evidence(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "evidence"
    __table_args__ = (Index("ix_evidence_org_answer", "organization_id", "answer_id"),)

    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    answer_id: Mapped[UUID] = mapped_column(
        ForeignKey("answers.id", ondelete="CASCADE"), index=True
    )
    uploaded_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    file_name: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(Integer)
    storage_key: Mapped[str] = mapped_column(String(500), unique=True)
    sha256: Mapped[str] = mapped_column(String(64))
