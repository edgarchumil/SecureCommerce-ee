from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.fallback import fallback_recommendation
from app.ai.provider import PROMPT_VERSION, AIProvider, get_ai_provider
from app.core.config import settings
from app.core.database import get_db
from app.models.ai import AIRecommendation, RecommendationStatus
from app.models.assets import Asset
from app.models.risks import Risk, Threat, Vulnerability
from app.schemas.ai import GenerateRequest, RecommendationResponse, RecommendedAction, ReviewRequest
from app.security.dependencies import Principal, require_permission
from app.security.permissions import Permission
from app.services.audit import add_audit

router = APIRouter(prefix="/ai/recommendations", tags=["inteligencia artificial"])


def _org(principal: Principal) -> UUID:
    if principal.organization_id is None:
        raise HTTPException(status_code=403, detail="Seleccione una organización")
    return principal.organization_id


def _response(item: AIRecommendation) -> RecommendationResponse:
    return RecommendationResponse(
        id=item.id,
        risk_id=item.risk_id,
        kind=item.kind,
        status=item.status,
        title=item.title,
        summary=item.summary,
        actions=[RecommendedAction.model_validate(action) for action in item.actions],
        references=item.references,
        provider=item.provider,
        model=item.model,
        prompt_version=item.prompt_version,
        is_fallback=item.is_fallback,
        input_tokens=item.input_tokens,
        output_tokens=item.output_tokens,
        estimated_cost_usd=item.estimated_cost_usd,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


async def _risk_payload(
    db: AsyncSession, risk_id: UUID, organization_id: UUID, kind: str
) -> dict[str, object]:
    row = (
        await db.execute(
            select(Risk, Asset.asset_type, Threat.likelihood, Vulnerability.severity)
            .join(Asset, Risk.asset_id == Asset.id)
            .outerjoin(Threat, Risk.threat_id == Threat.id)
            .outerjoin(Vulnerability, Risk.vulnerability_id == Vulnerability.id)
            .where(
                Risk.id == risk_id,
                Risk.organization_id == organization_id,
                Risk.deleted_at.is_(None),
            )
        )
    ).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Riesgo no encontrado")
    risk, asset_type, likelihood, severity = row
    return {
        "kind": kind,
        "code": risk.code,
        "asset_type": str(asset_type),
        "probability": risk.probability,
        "impact": risk.impact,
        "inherent_score": risk.inherent_score,
        "inherent_level": str(risk.inherent_level),
        "residual_probability": risk.residual_probability,
        "residual_impact": risk.residual_impact,
        "residual_score": risk.residual_score,
        "residual_level": str(risk.residual_level),
        "treatment_strategy": str(risk.treatment_strategy),
        "threat_likelihood": likelihood,
        "vulnerability_severity": severity,
        "has_existing_controls": bool(risk.existing_controls),
    }


@router.post("/generate", response_model=RecommendationResponse, status_code=201)
async def generate_recommendation(
    payload: GenerateRequest,
    request: Request,
    provider: AIProvider = Depends(get_ai_provider),
    principal: Principal = Depends(require_permission(Permission.AI_GENERATE)),
    db: AsyncSession = Depends(get_db),
) -> RecommendationResponse:
    organization_id = _org(principal)
    minimal = await _risk_payload(db, payload.risk_id, organization_id, payload.kind.value)
    month_start = datetime.now(UTC).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    spent = await db.scalar(
        select(func.sum(AIRecommendation.estimated_cost_usd)).where(
            AIRecommendation.organization_id == organization_id,
            AIRecommendation.created_at >= month_start,
        )
    )
    use_external = (
        settings.ai_enabled
        and bool(settings.openai_api_key)
        and float(spent or 0) < settings.ai_monthly_budget_limit
    )
    result = fallback_recommendation(minimal)
    if use_external:
        try:
            result = await provider.generate(minimal)
        except Exception:  # provider failures must not expose internals or block the user
            result = fallback_recommendation(minimal)
    estimated_cost = round(
        result.input_tokens / 1_000_000 * settings.ai_input_cost_per_million
        + result.output_tokens / 1_000_000 * settings.ai_output_cost_per_million,
        6,
    )
    item = AIRecommendation(
        organization_id=organization_id,
        risk_id=payload.risk_id,
        created_by=principal.user.id,
        kind=payload.kind,
        title=result.content.title,
        summary=result.content.summary,
        actions=[action.model_dump() for action in result.content.actions],
        references=result.content.references,
        provider=result.provider,
        model=result.model,
        prompt_version=PROMPT_VERSION,
        is_fallback=result.provider == "local",
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        estimated_cost_usd=estimated_cost,
    )
    db.add(item)
    await db.flush()
    add_audit(
        db,
        request,
        "ai.recommendation.generate",
        "ai_recommendation",
        "success",
        user_id=principal.user.id,
        organization_id=organization_id,
        resource_id=str(item.id),
        changes={
            "provider": item.provider,
            "model": item.model,
            "prompt_version": item.prompt_version,
            "fallback": item.is_fallback,
            "estimated_cost_usd": estimated_cost,
        },
    )
    await db.commit()
    return _response(item)


@router.get("", response_model=list[RecommendationResponse])
async def list_recommendations(
    risk_id: UUID | None = None,
    principal: Principal = Depends(require_permission(Permission.AI_READ)),
    db: AsyncSession = Depends(get_db),
) -> list[RecommendationResponse]:
    filters = [AIRecommendation.organization_id == _org(principal)]
    if risk_id:
        filters.append(AIRecommendation.risk_id == risk_id)
    items = (
        await db.scalars(
            select(AIRecommendation).where(*filters).order_by(AIRecommendation.created_at.desc())
        )
    ).all()
    return [_response(item) for item in items]


@router.patch("/{recommendation_id}", response_model=RecommendationResponse)
async def review_recommendation(
    recommendation_id: UUID,
    payload: ReviewRequest,
    request: Request,
    principal: Principal = Depends(require_permission(Permission.AI_REVIEW)),
    db: AsyncSession = Depends(get_db),
) -> RecommendationResponse:
    organization_id = _org(principal)
    item = await db.scalar(
        select(AIRecommendation).where(
            AIRecommendation.id == recommendation_id,
            AIRecommendation.organization_id == organization_id,
        )
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Recomendación no encontrada")
    if item.status != RecommendationStatus.DRAFT:
        raise HTTPException(status_code=409, detail="La recomendación ya fue revisada")
    if payload.title is not None:
        item.title = payload.title
    if payload.summary is not None:
        item.summary = payload.summary
    if payload.actions is not None:
        item.actions = [action.model_dump() for action in payload.actions]
    item.status = payload.status
    item.reviewed_by = principal.user.id
    add_audit(
        db,
        request,
        "ai.recommendation.review",
        "ai_recommendation",
        "success",
        user_id=principal.user.id,
        organization_id=organization_id,
        resource_id=str(item.id),
        changes={"status": payload.status.value},
    )
    await db.commit()
    return _response(item)
