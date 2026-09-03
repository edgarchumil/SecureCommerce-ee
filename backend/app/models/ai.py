from enum import StrEnum
from uuid import UUID

from sqlalchemy import JSON, Boolean, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class RecommendationKind(StrEnum):
    RISK_EXPLANATION = "risk_explanation"
    PRIORITIZATION = "prioritization"
    TREATMENT_PLAN = "treatment_plan"
    EXECUTIVE_SUMMARY = "executive_summary"


class RecommendationStatus(StrEnum):
    DRAFT = "draft"
    APPROVED = "approved"
    REJECTED = "rejected"


class AIRecommendation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_recommendations"
    __table_args__ = (
        Index("ix_ai_recommendations_org_status", "organization_id", "status"),
        Index("ix_ai_recommendations_org_risk", "organization_id", "risk_id"),
    )

    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    risk_id: Mapped[UUID | None] = mapped_column(ForeignKey("risks.id"), nullable=True)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    reviewed_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    kind: Mapped[RecommendationKind] = mapped_column(String(40))
    status: Mapped[RecommendationStatus] = mapped_column(
        String(20), default=RecommendationStatus.DRAFT
    )
    title: Mapped[str] = mapped_column(String(220))
    summary: Mapped[str] = mapped_column(Text)
    actions: Mapped[list[dict[str, str]]] = mapped_column(JSON)
    references: Mapped[list[str]] = mapped_column(JSON)
    provider: Mapped[str] = mapped_column(String(40))
    model: Mapped[str] = mapped_column(String(100))
    prompt_version: Mapped[str] = mapped_column(String(30))
    is_fallback: Mapped[bool] = mapped_column(Boolean, default=False)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost_usd: Mapped[float] = mapped_column(Float, default=0)
