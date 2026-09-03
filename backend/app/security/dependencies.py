from dataclasses import dataclass
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.identity import Membership, Organization, RoleCode, User
from app.security.permissions import Permission, has_permission
from app.security.tokens import decode_access_token

bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Principal:
    user: User
    organization_id: UUID | None
    role: RoleCode | None


async def get_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> Principal:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Sesión inválida o expirada",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = UUID(payload["sub"])
        organization_id = UUID(payload["org"]) if payload.get("org") else None
        role = RoleCode(payload["role"]) if payload.get("role") else None
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise unauthorized from None

    user = await db.scalar(select(User).where(User.id == user_id, User.deleted_at.is_(None)))
    if user is None or not user.is_active:
        raise unauthorized
    if organization_id is not None:
        membership = await db.scalar(
            select(Membership).join(Organization).where(
                Membership.user_id == user.id,
                Membership.organization_id == organization_id,
                Membership.role_code == role,
                Membership.is_active.is_(True),
                Membership.deleted_at.is_(None),
                Organization.is_active.is_(True),
                Organization.deleted_at.is_(None),
            )
        )
        if membership is None:
            raise unauthorized
    return Principal(user=user, organization_id=organization_id, role=role)


def require_permission(permission: Permission):  # type: ignore[no-untyped-def]
    async def dependency(principal: Principal = Depends(get_principal)) -> Principal:
        if principal.role is None or not has_permission(principal.role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Permiso insuficiente"
            )
        return principal

    return dependency
