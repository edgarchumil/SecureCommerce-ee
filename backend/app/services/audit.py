from typing import Any
from uuid import UUID

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import utc_now
from app.models.identity import AuditLog

SENSITIVE_KEYS = {"password", "token", "secret", "mfa_code", "refresh_token"}


def sanitize_changes(changes: dict[str, Any] | None) -> dict[str, Any] | None:
    if changes is None:
        return None
    return {key: value for key, value in changes.items() if key.lower() not in SENSITIVE_KEYS}


def add_audit(
    db: AsyncSession,
    request: Request,
    action: str,
    resource_type: str,
    result: str,
    *,
    user_id: UUID | None = None,
    organization_id: UUID | None = None,
    resource_id: str | None = None,
    changes: dict[str, Any] | None = None,
) -> AuditLog:
    forwarded = request.headers.get("X-Forwarded-For")
    ip_address = (
        forwarded.split(",")[0].strip()
        if forwarded
        else (request.client.host if request.client else None)
    )
    log = AuditLog(
        user_id=user_id,
        organization_id=organization_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        result=result,
        ip_address=ip_address,
        user_agent=request.headers.get("User-Agent", "")[:500] or None,
        correlation_id=getattr(request.state, "correlation_id", None),
        changes=sanitize_changes(changes),
        created_at=utc_now(),
    )
    db.add(log)
    return log
