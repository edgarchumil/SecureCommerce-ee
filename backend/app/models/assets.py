from datetime import date
from enum import StrEnum
from uuid import UUID

from sqlalchemy import JSON, Date, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class AssetType(StrEnum):
    SERVER = "server"
    COMPUTER = "computer"
    MOBILE = "mobile"
    NETWORK = "network"
    APPLICATION = "application"
    DATABASE = "database"
    INFORMATION = "information"
    CLOUD_SERVICE = "cloud_service"
    CRITICAL_ACCOUNT = "critical_account"
    SUPPLIER = "supplier"
    OTHER = "other"


class AssetStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    RETIRED = "retired"


class ExposureLevel(StrEnum):
    INTERNAL = "internal"
    LIMITED = "limited"
    PUBLIC = "public"


class Asset(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "assets"
    __table_args__ = (
        UniqueConstraint("organization_id", "internal_code", name="uq_assets_org_code"),
        Index("ix_assets_org_type_status", "organization_id", "asset_type", "status"),
        Index("ix_assets_org_criticality", "organization_id", "overall_criticality"),
    )

    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(180))
    internal_code: Mapped[str] = mapped_column(String(80))
    asset_type: Mapped[AssetType] = mapped_column(String(32))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner: Mapped[str | None] = mapped_column(String(160), nullable=True)
    technical_owner: Mapped[str | None] = mapped_column(String(160), nullable=True)
    location: Mapped[str | None] = mapped_column(String(180), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    operating_system: Mapped[str | None] = mapped_column(String(120), nullable=True)
    manufacturer: Mapped[str | None] = mapped_column(String(120), nullable=True)
    model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    exposure_level: Mapped[ExposureLevel] = mapped_column(String(20))
    status: Mapped[AssetStatus] = mapped_column(String(20))
    acquisition_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    confidentiality_criticality: Mapped[int] = mapped_column(Integer)
    integrity_criticality: Mapped[int] = mapped_column(Integer)
    availability_criticality: Mapped[int] = mapped_column(Integer)
    overall_criticality: Mapped[int] = mapped_column(Integer)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    outgoing_dependencies: Mapped[list["AssetDependency"]] = relationship(
        foreign_keys="AssetDependency.asset_id", cascade="all, delete-orphan"
    )


class AssetDependency(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "asset_dependencies"
    __table_args__ = (
        UniqueConstraint("asset_id", "depends_on_asset_id", name="uq_asset_dependency_pair"),
    )

    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    asset_id: Mapped[UUID] = mapped_column(ForeignKey("assets.id", ondelete="CASCADE"), index=True)
    depends_on_asset_id: Mapped[UUID] = mapped_column(
        ForeignKey("assets.id", ondelete="CASCADE"), index=True
    )
