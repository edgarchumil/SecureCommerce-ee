from typing import Literal

from fastapi import APIRouter, Response, status
from sqlalchemy import text

from app.core.database import engine
from app.core.redis import redis_client
from app.schemas.health import DependencyStatus, ReadinessResponse

router = APIRouter(prefix="/health", tags=["salud"])


async def database_is_ready() -> bool:
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return True
    except Exception:  # no se exponen detalles de infraestructura
        return False


async def redis_is_ready() -> bool:
    try:
        await redis_client.ping()
        return True
    except Exception:  # no se exponen detalles de infraestructura
        return False


@router.get("/live")
async def liveness() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready", response_model=ReadinessResponse)
async def readiness(response: Response) -> ReadinessResponse:
    checks: dict[str, DependencyStatus] = {}
    checks["database"] = DependencyStatus(status="ok" if await database_is_ready() else "error")
    checks["redis"] = DependencyStatus(status="ok" if await redis_is_ready() else "error")

    overall: Literal["ok", "degraded"] = (
        "ok" if all(item.status == "ok" for item in checks.values()) else "degraded"
    )
    if overall == "degraded":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadinessResponse(status=overall, services=checks)
