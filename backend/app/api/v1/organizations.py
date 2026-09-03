import secrets
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.identity import AuditLog, Membership, Organization, User
from app.schemas.identity import (
    AuditLogResponse,
    InviteMemberRequest,
    MembershipResponse,
    OrganizationResponse,
    OrganizationUpdate,
    UpdateRoleRequest,
)
from app.security.dependencies import Principal, require_permission
from app.security.passwords import hash_password
from app.security.permissions import Permission
from app.services.audit import add_audit

router = APIRouter(tags=["organizaciones"])


def _require_org(principal: Principal) -> UUID:
    if principal.organization_id is None:
        raise HTTPException(status_code=403, detail="Seleccione una organización")
    return principal.organization_id


@router.get("/organizations/current", response_model=OrganizationResponse)
async def current_organization(
    principal: Principal = Depends(require_permission(Permission.ORGANIZATION_READ)),
    db: AsyncSession = Depends(get_db),
) -> Organization:
    organization_id = _require_org(principal)
    organization = await db.scalar(
        select(Organization).where(
            Organization.id == organization_id,
            Organization.is_active.is_(True),
            Organization.deleted_at.is_(None),
        )
    )
    if organization is None:
        raise HTTPException(status_code=404, detail="Organización no encontrada")
    return organization


@router.get("/memberships", response_model=list[MembershipResponse])
@router.get("/users", response_model=list[MembershipResponse])
async def list_memberships(
    principal: Principal = Depends(require_permission(Permission.MEMBERSHIP_READ)),
    db: AsyncSession = Depends(get_db),
) -> list[MembershipResponse]:
    organization_id = _require_org(principal)
    memberships = (
        await db.scalars(
            select(Membership)
            .options(selectinload(Membership.user))
            .where(
                Membership.organization_id == organization_id,
                Membership.deleted_at.is_(None),
            )
            .order_by(Membership.created_at)
        )
    ).all()
    return [
        MembershipResponse(
            id=item.id,
            user_id=item.user_id,
            email=item.user.email,
            full_name=item.user.full_name,
            role_code=item.role_code,
            is_active=item.is_active,
        )
        for item in memberships
    ]


@router.patch("/organizations/current", response_model=OrganizationResponse)
async def update_current_organization(
    payload: OrganizationUpdate,
    request: Request,
    principal: Principal = Depends(require_permission(Permission.ORGANIZATION_UPDATE)),
    db: AsyncSession = Depends(get_db),
) -> Organization:
    organization_id = _require_org(principal)
    organization = await db.scalar(
        select(Organization).where(
            Organization.id == organization_id,
            Organization.deleted_at.is_(None),
        )
    )
    if organization is None:
        raise HTTPException(status_code=404, detail="Organización no encontrada")
    changes = payload.model_dump(exclude_none=True)
    for field, value in changes.items():
        setattr(organization, field, value)
    add_audit(
        db,
        request,
        "organization.update",
        "organization",
        "success",
        user_id=principal.user.id,
        organization_id=organization_id,
        resource_id=str(organization.id),
        changes=changes,
    )
    await db.commit()
    return organization


@router.post("/memberships/invite", response_model=MembershipResponse, status_code=201)
async def invite_member(
    payload: InviteMemberRequest,
    request: Request,
    principal: Principal = Depends(require_permission(Permission.MEMBERSHIP_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> MembershipResponse:
    organization_id = _require_org(principal)
    email = payload.email.lower()
    user = await db.scalar(select(User).where(User.email == email, User.deleted_at.is_(None)))
    if user is None:
        user = User(
            email=email,
            full_name=payload.full_name,
            password_hash=hash_password(secrets.token_urlsafe(32)),
            is_active=False,
        )
        db.add(user)
        await db.flush()
    existing = await db.scalar(
        select(Membership).where(
            Membership.organization_id == organization_id,
            Membership.user_id == user.id,
            Membership.deleted_at.is_(None),
        )
    )
    if existing is not None:
        raise HTTPException(status_code=409, detail="La persona ya pertenece a la organización")
    membership = Membership(
        organization_id=organization_id,
        user_id=user.id,
        role_code=payload.role_code,
        is_active=True,
    )
    db.add(membership)
    await db.flush()
    add_audit(
        db,
        request,
        "membership.invite",
        "membership",
        "success",
        user_id=principal.user.id,
        organization_id=organization_id,
        resource_id=str(membership.id),
        changes={"invited_email": email, "role": payload.role_code.value},
    )
    await db.commit()
    return MembershipResponse(
        id=membership.id,
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        role_code=membership.role_code,
        is_active=membership.is_active,
    )


@router.patch("/memberships/{membership_id}/role", response_model=MembershipResponse)
async def update_member_role(
    membership_id: UUID,
    payload: UpdateRoleRequest,
    request: Request,
    principal: Principal = Depends(require_permission(Permission.MEMBERSHIP_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> MembershipResponse:
    organization_id = _require_org(principal)
    membership = await db.scalar(
        select(Membership)
        .options(selectinload(Membership.user))
        .where(
            Membership.id == membership_id,
            Membership.organization_id == organization_id,
            Membership.deleted_at.is_(None),
        )
    )
    if membership is None:
        raise HTTPException(status_code=404, detail="Membresía no encontrada")
    previous = membership.role_code
    membership.role_code = payload.role_code
    add_audit(
        db,
        request,
        "membership.role.update",
        "membership",
        "success",
        user_id=principal.user.id,
        organization_id=organization_id,
        resource_id=str(membership.id),
        changes={"previous": str(previous), "new": payload.role_code.value},
    )
    await db.commit()
    return MembershipResponse(
        id=membership.id,
        user_id=membership.user_id,
        email=membership.user.email,
        full_name=membership.user.full_name,
        role_code=membership.role_code,
        is_active=membership.is_active,
    )


@router.get("/audit-logs", response_model=list[AuditLogResponse])
async def list_audit_logs(
    principal: Principal = Depends(require_permission(Permission.AUDIT_READ)),
    db: AsyncSession = Depends(get_db),
) -> list[AuditLog]:
    organization_id = _require_org(principal)
    return list(
        (
            await db.scalars(
                select(AuditLog)
                .where(AuditLog.organization_id == organization_id)
                .order_by(AuditLog.created_at.desc())
                .limit(100)
            )
        ).all()
    )
