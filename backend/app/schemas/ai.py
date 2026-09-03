from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.ai import RecommendationKind, RecommendationStatus


class RecommendedAction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: str = Field(min_length=3, max_length=500)
    rationale: str = Field(min_length=3, max_length=800)
    priority: str = Field(pattern="^(alta|media|baja)$")


class GeneratedContent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=3, max_length=220)
    summary: str = Field(min_length=10, max_length=3000)
    actions: list[RecommendedAction] = Field(min_length=1, max_length=6)
    references: list[str] = Field(min_length=1, max_length=6)
    disclaimer: str = Field(min_length=10, max_length=500)

    @field_validator("references")
    @classmethod
    def approved_references(cls, values: list[str]) -> list[str]:
        approved = ("NIST CSF 2.0", "CIS Controls v8", "OWASP")
        if any(not value.startswith(approved) for value in values):
            raise ValueError("La referencia no pertenece al catálogo aprobado")
        return values


class GenerateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    risk_id: UUID
    kind: RecommendationKind = RecommendationKind.TREATMENT_PLAN


class ReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: RecommendationStatus
    title: str | None = Field(default=None, min_length=3, max_length=220)
    summary: str | None = Field(default=None, min_length=10, max_length=3000)
    actions: list[RecommendedAction] | None = Field(default=None, max_length=6)


class RecommendationResponse(BaseModel):
    id: UUID
    risk_id: UUID | None
    kind: RecommendationKind
    status: RecommendationStatus
    title: str
    summary: str
    actions: list[RecommendedAction]
    references: list[str]
    provider: str
    model: str
    prompt_version: str
    is_fallback: bool
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float
    created_at: datetime
    updated_at: datetime


class ProviderResult(BaseModel):
    content: GeneratedContent
    provider: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
