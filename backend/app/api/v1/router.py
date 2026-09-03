from fastapi import APIRouter

from app.api.v1.ai import router as ai_router
from app.api.v1.assets import router as assets_router
from app.api.v1.auth import router as auth_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.evaluations import framework_router
from app.api.v1.evaluations import router as evaluations_router
from app.api.v1.health import router as health_router
from app.api.v1.operations import incident_router, notification_router
from app.api.v1.organizations import router as organizations_router
from app.api.v1.platform import router as platform_router
from app.api.v1.reports import router as reports_router
from app.api.v1.risks import router as risks_router
from app.api.v1.sessions import router as sessions_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(assets_router)
api_router.include_router(auth_router)
api_router.include_router(organizations_router)
api_router.include_router(sessions_router)
api_router.include_router(framework_router)
api_router.include_router(evaluations_router)
api_router.include_router(risks_router)
api_router.include_router(dashboard_router)
api_router.include_router(ai_router)
api_router.include_router(reports_router)
api_router.include_router(incident_router)
api_router.include_router(notification_router)
api_router.include_router(platform_router)
