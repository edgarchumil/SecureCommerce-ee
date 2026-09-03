from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.base import utc_now
from app.models.identity import Session
from app.schemas.identity import SessionResponse
from app.security.dependencies import Principal, get_principal
from app.services.audit import add_audit

router = APIRouter(prefix="/sessions", tags=["sesiones"])


@router.get("", response_model=list[SessionResponse])
async def list_sessions(
    principal: Principal = Depends(get_principal), db: AsyncSession = Depends(get_db)
) -> list[Session]:
    return list(
        (
            await db.scalars(
                select(Session)
                .where(Session.user_id == principal.user.id)
                .order_by(Session.created_at.desc())
            )
        ).all()
    )


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_session(
    session_id: UUID,
    request: Request,
    principal: Principal = Depends(get_principal),
    db: AsyncSession = Depends(get_db),
) -> None:
    session = await db.scalar(
        select(Session).where(Session.id == session_id, Session.user_id == principal.user.id)
    )
    if session is None:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    if session.revoked_at is None:
        session.revoked_at = utc_now()
        add_audit(
            db,
            request,
            "session.revoke",
            "session",
            "success",
            user_id=principal.user.id,
            organization_id=principal.organization_id,
            resource_id=str(session.id),
        )
        await db.commit()
