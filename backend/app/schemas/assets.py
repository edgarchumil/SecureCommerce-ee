from datetime import date, datetime
from ipaddress import ip_address
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.assets import AssetStatus, AssetType, ExposureLevel


class AssetFields(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=2, max_length=180)
    internal_code: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9._-]+$")
    asset_type: AssetType
    description: str | None = Field(default=None, max_length=4000)
    owner: str | None = Field(default=None, max_length=160)
    technical_owner: str | None = Field(default=None, max_length=160)
    location: str | None = Field(default=None, max_length=180)
    ip_address: str | None = None
    operating_system: str | None = Field(default=None, max_length=120)
    manufacturer: str | None = Field(default=None, max_length=120)
    model: str | None = Field(default=None, max_length=120)
    exposure_level: ExposureLevel = ExposureLevel.INTERNAL
    status: AssetStatus = AssetStatus.ACTIVE
    acquisition_date: date | None = None
    confidentiality_criticality: int = Field(ge=1, le=5)
    integrity_criticality: int = Field(ge=1, le=5)
    availability_criticality: int = Field(ge=1, le=5)
    tags: list[str] = Field(default_factory=list, max_length=20)
    notes: str | None = Field(default=None, max_length=4000)
    dependency_ids: list[UUID] = Field(default_factory=list, max_length=50)

    @field_validator("ip_address")
    @classmethod
    def valid_ip(cls, value: str | None) -> str | None:
        if value:
            ip_address(value)
        return value

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, value: list[str]) -> list[str]:
        cleaned = [tag.strip().lower() for tag in value if tag.strip()]
        if any(len(tag) > 40 for tag in cleaned):
            raise ValueError("Cada etiqueta debe tener máximo 40 caracteres")
        return list(dict.fromkeys(cleaned))


class AssetCreate(AssetFields):
    pass


class AssetUpdate(AssetFields):
    pass


class AssetResponse(AssetFields):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    organization_id: UUID
    overall_criticality: int
    created_at: datetime
    updated_at: datetime


class AssetPage(BaseModel):
    items: list[AssetResponse]
    total: int
    page: int
    page_size: int
    pages: int
