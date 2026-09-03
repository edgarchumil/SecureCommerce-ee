from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.evaluations import EvaluationStatus


class FrameworkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    code: str
    name: str
    version: str
    description: str | None


class QuestionResponse(BaseModel):
    id: UUID
    function_code: str
    function_name: str
    category_code: str
    category_name: str
    control_code: str
    text: str
    help_text: str
    weight: float
    expected_evidence: str
    response_options: list[dict[str, object]]
    base_recommendation: str


class EvaluationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    framework_id: UUID
    code: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9._-]+$")
    name: str = Field(min_length=2, max_length=180)
    scope: str = Field(min_length=5, max_length=4000)
    target_maturity: int = Field(default=3, ge=0, le=4)
    comments: str | None = Field(default=None, max_length=4000)
    asset_ids: list[UUID] = Field(default_factory=list, max_length=200)


class EvaluationResponse(BaseModel):
    id: UUID
    framework_id: UUID
    code: str
    name: str
    scope: str
    target_maturity: int
    status: EvaluationStatus
    version: int
    comments: str | None
    asset_ids: list[UUID]
    created_at: datetime
    updated_at: datetime


class AnswerUpsert(BaseModel):
    maturity: int = Field(ge=0, le=4)
    comment: str | None = Field(default=None, max_length=2000)


class AnswerResponse(BaseModel):
    id: UUID
    question_id: UUID
    maturity: int
    comment: str | None
    updated_at: datetime


class EvidenceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    file_name: str = Field(min_length=1, max_length=255)
    content_type: str = Field(pattern=r"^(application/pdf|image/png|image/jpeg|text/plain)$")
    size_bytes: int = Field(gt=0, le=10_485_760)
    sha256: str = Field(pattern=r"^[a-fA-F0-9]{64}$")


class StatusUpdate(BaseModel):
    status: EvaluationStatus


class ScoreItem(BaseModel):
    code: str
    name: str
    score: float
    target: float
    gap: float
    answered: int
    total: int


class EvaluationResults(BaseModel):
    current_profile: float
    target_profile: float
    gap: float
    answered: int
    total: int
    by_function: list[ScoreItem]
    by_category: list[ScoreItem]
