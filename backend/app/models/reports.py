from enum import StrEnum
from uuid import UUID

from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ReportType(StrEnum):
    EXECUTIVE = "executive"
    TECHNICAL = "technical"


class ReportStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Report(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "reports"
    __table_args__ = (Index("ix_reports_org_status", "organization_id", "status"),)

    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    report_type: Mapped[ReportType] = mapped_column(String(20))
    status: Mapped[ReportStatus] = mapped_column(String(20), default=ReportStatus.PENDING)
    title: Mapped[str] = mapped_column(String(220))
    scope: Mapped[str] = mapped_column(Text)
    storage_key: Mapped[str | None] = mapped_column(String(500), unique=True, nullable=True)
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
