from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.risks import RiskLevel, RiskStatus, TreatmentStrategy


class CatalogCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=2, max_length=180)
    description: str = Field(min_length=3, max_length=4000)
    rating: int = Field(ge=1, le=5)


class CatalogResponse(BaseModel):
    id: UUID
    name: str
    description: str
    rating: int


class RiskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9._-]+$")
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=3, max_length=4000)
    asset_id: UUID
    threat_id: UUID | None = None
    vulnerability_id: UUID | None = None
    probability: int = Field(ge=1, le=5)
    impact: int = Field(ge=1, le=5)
    existing_controls: str | None = Field(default=None, max_length=4000)
    residual_probability: int = Field(ge=1, le=5)
    residual_impact: int = Field(ge=1, le=5)
    treatment_strategy: TreatmentStrategy
    responsible_user_id: UUID | None = None
    target_date: date | None = None
    progress: int = Field(default=0, ge=0, le=100)
    status: RiskStatus = RiskStatus.IDENTIFIED


class RiskUpdate(RiskCreate):
    pass


class RiskResponse(RiskCreate):
    id: UUID
    organization_id: UUID
    inherent_score: int
    inherent_level: RiskLevel
    residual_score: int
    residual_level: RiskLevel
    created_at: datetime
    updated_at: datetime


class RiskPage(BaseModel):
    items: list[RiskResponse]
    total: int
    page: int
    page_size: int
    pages: int


class TreatmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: str = Field(min_length=3, max_length=4000)
    responsible_user_id: UUID | None = None
    target_date: date | None = None
    progress: int = Field(default=0, ge=0, le=100)
    notes: str | None = Field(default=None, max_length=4000)


class TreatmentResponse(TreatmentCreate):
    id: UUID
    risk_id: UUID
    created_at: datetime
    updated_at: datetime


class RiskBandsUpdate(BaseModel):
    bands: list[dict[str, int | str]] = Field(min_length=4, max_length=4)
