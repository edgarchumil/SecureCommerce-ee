from datetime import date
from enum import StrEnum
from uuid import UUID

from sqlalchemy import JSON, Date, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskStatus(StrEnum):
    IDENTIFIED = "identified"
    ANALYZING = "analyzing"
    IN_TREATMENT = "in_treatment"
    ACCEPTED = "accepted"
    CLOSED = "closed"


class TreatmentStrategy(StrEnum):
    AVOID = "avoid"
    MITIGATE = "mitigate"
    TRANSFER = "transfer"
    ACCEPT = "accept"


class Vulnerability(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "vulnerabilities"
    __table_args__ = (Index("ix_vulnerabilities_org_name", "organization_id", "name"),)

    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(180))
    description: Mapped[str] = mapped_column(Text)
    severity: Mapped[int] = mapped_column(Integer)


class Threat(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "threats"
    __table_args__ = (Index("ix_threats_org_name", "organization_id", "name"),)

    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(180))
    description: Mapped[str] = mapped_column(Text)
    likelihood: Mapped[int] = mapped_column(Integer)


class Risk(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "risks"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_risks_org_code"),
        Index("ix_risks_org_level_status", "organization_id", "inherent_level", "status"),
        Index("ix_risks_org_target", "organization_id", "target_date"),
    )

    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    code: Mapped[str] = mapped_column(String(80))
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    asset_id: Mapped[UUID] = mapped_column(ForeignKey("assets.id"), index=True)
    threat_id: Mapped[UUID | None] = mapped_column(ForeignKey("threats.id"), nullable=True)
    vulnerability_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("vulnerabilities.id"), nullable=True
    )
    probability: Mapped[int] = mapped_column(Integer)
    impact: Mapped[int] = mapped_column(Integer)
    inherent_score: Mapped[int] = mapped_column(Integer)
    inherent_level: Mapped[RiskLevel] = mapped_column(String(20))
    existing_controls: Mapped[str | None] = mapped_column(Text, nullable=True)
    residual_probability: Mapped[int] = mapped_column(Integer)
    residual_impact: Mapped[int] = mapped_column(Integer)
    residual_score: Mapped[int] = mapped_column(Integer)
    residual_level: Mapped[RiskLevel] = mapped_column(String(20))
    treatment_strategy: Mapped[TreatmentStrategy] = mapped_column(String(20))
    responsible_user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[RiskStatus] = mapped_column(String(30), default=RiskStatus.IDENTIFIED)
    treatments: Mapped[list["RiskTreatment"]] = relationship(cascade="all, delete-orphan")


class RiskTreatment(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "risk_treatments"
    __table_args__ = (Index("ix_treatments_org_risk", "organization_id", "risk_id"),)

    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    risk_id: Mapped[UUID] = mapped_column(ForeignKey("risks.id", ondelete="CASCADE"), index=True)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(Text)
    responsible_user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class SystemSetting(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "system_settings"
    __table_args__ = (UniqueConstraint("organization_id", "key", name="uq_settings_org_key"),)

    organization_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("organizations.id"), nullable=True, index=True
    )
    key: Mapped[str] = mapped_column(String(100))
    value: Mapped[dict[str, object]] = mapped_column(JSON)
    updated_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
