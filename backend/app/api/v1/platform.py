from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.identity import Membership, Organization
from app.schemas.identity import PlatformOrganizationResponse, PlatformOrganizationUpdate
from app.security.dependencies import Principal, get_principal
from app.services.audit import add_audit

router = APIRouter(prefix="/platform", tags=["plataforma"])


def require_superadmin(principal: Principal = Depends(get_principal)) -> Principal:
    if not principal.user.is_superadmin:
        raise HTTPException(status_code=403, detail="Acceso exclusivo de plataforma")
    return principal


@router.get("/organizations", response_model=list[PlatformOrganizationResponse])
async def list_platform_organizations(
    _: Principal = Depends(require_superadmin), db: AsyncSession = Depends(get_db)
) -> list[PlatformOrganizationResponse]:
    rows = (
        await db.execute(
            select(Organization, func.count(Membership.id))
            .outerjoin(
                Membership,
                (Membership.organization_id == Organization.id)
                & Membership.deleted_at.is_(None),
            )
            .where(Organization.deleted_at.is_(None))
            .group_by(Organization.id)
            .order_by(Organization.name)
        )
    ).all()
    return [
        PlatformOrganizationResponse(
            id=org.id,
            name=org.name,
            slug=org.slug,
            sector=org.sector,
            size=org.size,
            country=org.country,
            is_active=org.is_active,
            member_count=count,
        )
        for org, count in rows
    ]


@router.patch("/organizations/{organization_id}", response_model=PlatformOrganizationResponse)
async def update_platform_organization(
    organization_id: UUID,
    payload: PlatformOrganizationUpdate,
    request: Request,
    principal: Principal = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
) -> PlatformOrganizationResponse:
    organization = await db.scalar(
        select(Organization).where(
            Organization.id == organization_id, Organization.deleted_at.is_(None)
        )
    )
    if organization is None:
        raise HTTPException(status_code=404, detail="Organización no encontrada")
    organization.is_active = payload.is_active
    add_audit(
        db,
        request,
        "platform.organization.status",
        "organization",
        "success",
        user_id=principal.user.id,
        organization_id=organization.id,
        resource_id=str(organization.id),
        changes={"is_active": payload.is_active},
    )
    await db.commit()
    count = await db.scalar(
        select(func.count(Membership.id)).where(
            Membership.organization_id == organization.id,
            Membership.deleted_at.is_(None),
        )
    )
    return PlatformOrganizationResponse(
        id=organization.id,
        name=organization.name,
        slug=organization.slug,
        sector=organization.sector,
        size=organization.size,
        country=organization.country,
        is_active=organization.is_active,
        member_count=count or 0,
    )
