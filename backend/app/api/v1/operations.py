from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.operations import Incident, IncidentStatus, Notification
from app.schemas.operations import (
    IncidentCreate,
    IncidentResponse,
    IncidentUpdate,
    NotificationResponse,
)
from app.security.dependencies import Principal, require_permission
from app.security.permissions import Permission
from app.services.audit import add_audit

incident_router = APIRouter(prefix="/incidents", tags=["incidentes"])
notification_router = APIRouter(prefix="/notifications", tags=["notificaciones"])


def _org(principal: Principal) -> UUID:
    if principal.organization_id is None:
        raise HTTPException(status_code=403, detail="Seleccione una organización")
    return principal.organization_id


async def _incident(db: AsyncSession, incident_id: UUID, organization_id: UUID) -> Incident:
    item = await db.scalar(
        select(Incident).where(
            Incident.id == incident_id,
            Incident.organization_id == organization_id,
            Incident.deleted_at.is_(None),
        )
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Incidente no encontrado")
    return item


@incident_router.get("", response_model=list[IncidentResponse])
async def list_incidents(
    principal: Principal = Depends(require_permission(Permission.INCIDENT_READ)),
    db: AsyncSession = Depends(get_db),
) -> list[Incident]:
    return list(
        (
            await db.scalars(
                select(Incident)
                .where(Incident.organization_id == _org(principal), Incident.deleted_at.is_(None))
                .order_by(Incident.occurred_at.desc())
                .limit(100)
            )
        ).all()
    )


@incident_router.post("", response_model=IncidentResponse, status_code=201)
async def create_incident(
    payload: IncidentCreate,
    request: Request,
    principal: Principal = Depends(require_permission(Permission.INCIDENT_WRITE)),
    db: AsyncSession = Depends(get_db),
) -> Incident:
    organization_id = _org(principal)
    item = Incident(
        organization_id=organization_id, created_by=principal.user.id, **payload.model_dump()
    )
    db.add(item)
    await db.flush()
    add_audit(
        db,
        request,
        "incident.create",
        "incident",
        "success",
        user_id=principal.user.id,
        organization_id=organization_id,
        resource_id=str(item.id),
    )
    await db.commit()
    return item


@incident_router.patch("/{incident_id}", response_model=IncidentResponse)
async def update_incident(
    incident_id: UUID,
    payload: IncidentUpdate,
    request: Request,
    principal: Principal = Depends(require_permission(Permission.INCIDENT_WRITE)),
    db: AsyncSession = Depends(get_db),
) -> Incident:
    organization_id = _org(principal)
    item = await _incident(db, incident_id, organization_id)
    changes = payload.model_dump(exclude_none=True)
    for field, value in changes.items():
        setattr(item, field, value)
    if payload.status == IncidentStatus.RESOLVED and item.resolved_at is None:
        item.resolved_at = datetime.now(UTC)
    elif payload.status is not None and payload.status != IncidentStatus.RESOLVED:
        item.resolved_at = None
    add_audit(
        db,
        request,
        "incident.update",
        "incident",
        "success",
        user_id=principal.user.id,
        organization_id=organization_id,
        resource_id=str(item.id),
        changes=changes,
    )
    await db.commit()
    return item


@incident_router.delete("/{incident_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_incident(
    incident_id: UUID,
    request: Request,
    principal: Principal = Depends(require_permission(Permission.INCIDENT_WRITE)),
    db: AsyncSession = Depends(get_db),
) -> None:
    organization_id = _org(principal)
    item = await _incident(db, incident_id, organization_id)
    item.deleted_at = datetime.now(UTC)
    add_audit(
        db,
        request,
        "incident.delete",
        "incident",
        "success",
        user_id=principal.user.id,
        organization_id=organization_id,
        resource_id=str(item.id),
    )
    await db.commit()


@notification_router.get("", response_model=list[NotificationResponse])
async def list_notifications(
    principal: Principal = Depends(require_permission(Permission.NOTIFICATION_READ)),
    db: AsyncSession = Depends(get_db),
) -> list[Notification]:
    return list(
        (
            await db.scalars(
                select(Notification)
                .where(
                    Notification.organization_id == _org(principal),
                    Notification.user_id == principal.user.id,
                )
                .order_by(Notification.created_at.desc())
                .limit(50)
            )
        ).all()
    )


@notification_router.patch("/{notification_id}/read", status_code=204)
async def read_notification(
    notification_id: UUID,
    principal: Principal = Depends(require_permission(Permission.NOTIFICATION_READ)),
    db: AsyncSession = Depends(get_db),
) -> None:
    item = await db.scalar(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.organization_id == _org(principal),
            Notification.user_id == principal.user.id,
        )
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    item.read_at = datetime.now(UTC)
    await db.commit()
