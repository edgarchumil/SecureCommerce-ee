from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.operations import IncidentSeverity, IncidentStatus


class IncidentCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=3, max_length=5000)
    severity: IncidentSeverity
    occurred_at: datetime


class IncidentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, min_length=3, max_length=5000)
    severity: IncidentSeverity | None = None
    status: IncidentStatus | None = None

    @model_validator(mode="after")
    def not_empty(self) -> "IncidentUpdate":
        if all(
            value is None for value in (self.title, self.description, self.severity, self.status)
        ):
            raise ValueError("Incluya al menos un cambio")
        return self


class IncidentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    title: str
    description: str
    severity: IncidentSeverity
    status: IncidentStatus
    occurred_at: datetime
    resolved_at: datetime | None
    created_at: datetime
    updated_at: datetime


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    title: str
    message: str
    link: str | None
    read_at: datetime | None
    created_at: datetime
