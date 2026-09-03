from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.reports import ReportStatus, ReportType


class ReportCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    report_type: ReportType
    title: str = Field(min_length=3, max_length=220)
    scope: str = Field(min_length=3, max_length=2000)


class ReportResponse(BaseModel):
    id: UUID
    report_type: ReportType
    status: ReportStatus
    title: str
    scope: str
    file_name: str | None
    size_bytes: int | None
    sha256: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime
    download_url: str | None
