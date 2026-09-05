from math import ceil
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.assets import Asset
from app.models.base import utc_now
from app.models.identity import Membership
from app.models.risks import (
    Risk,
    RiskLevel,
    RiskStatus,
    RiskTreatment,
    SystemSetting,
    Threat,
    Vulnerability,
)
from app.schemas.risks import (
    CatalogCreate,
    CatalogResponse,
    RiskBandsUpdate,
    RiskCreate,
    RiskPage,
    RiskResponse,
    RiskUpdate,
    TreatmentCreate,
    TreatmentResponse,
)
from app.security.dependencies import Principal, require_permission
from app.security.permissions import Permission
from app.services.audit import add_audit
from app.services.risk_engine import DEFAULT_BANDS, RiskBand, bands_from_setting, calculate_risk

router = APIRouter(tags=["riesgos"])


def _org(principal: Principal) -> UUID:
    if principal.organization_id is None:
        raise HTTPException(status_code=403, detail="Seleccione una organización")
    return principal.organization_id


async def _bands(db: AsyncSession, organization_id: UUID) -> tuple[RiskBand, ...]:
    setting = await db.scalar(
        select(SystemSetting)
        .where(
            SystemSetting.key == "risk_matrix_thresholds",
            or_(
                SystemSetting.organization_id == organization_id,
                SystemSetting.organization_id.is_(None),
            ),
        )
        .order_by(SystemSetting.organization_id.desc())
        .limit(1)
    )
    try:
        return bands_from_setting(setting.value if setting else None)
    except ValueError:
        return DEFAULT_BANDS


async def _related_exists(
    db: AsyncSession, model: type[Any], item_id: UUID | None, organization_id: UUID
) -> bool:
    if item_id is None:
        return True
    return (
        await db.scalar(
            select(model.id).where(
                model.id == item_id,
                model.organization_id == organization_id,
                model.deleted_at.is_(None),
            )
        )
        is not None
    )


async def _validate_relations(db: AsyncSession, payload: RiskCreate, organization_id: UUID) -> None:
    if not await _related_exists(db, Asset, payload.asset_id, organization_id):
        raise HTTPException(status_code=422, detail="Activo no válido")
    if not await _related_exists(db, Threat, payload.threat_id, organization_id):
        raise HTTPException(status_code=422, detail="Amenaza no válida")
    if not await _related_exists(db, Vulnerability, payload.vulnerability_id, organization_id):
        raise HTTPException(status_code=422, detail="Vulnerabilidad no válida")
    if payload.responsible_user_id is not None:
        member = await db.scalar(
            select(Membership.id).where(
                Membership.organization_id == organization_id,
                Membership.user_id == payload.responsible_user_id,
                Membership.is_active.is_(True),
                Membership.deleted_at.is_(None),
            )
        )
        if member is None:
            raise HTTPException(status_code=422, detail="Responsable no válido")


def _response(item: Risk) -> RiskResponse:
    return RiskResponse(
        **{field: getattr(item, field) for field in RiskCreate.model_fields},
        id=item.id,
        organization_id=item.organization_id,
        inherent_score=item.inherent_score,
        inherent_level=item.inherent_level,
        residual_score=item.residual_score,
        residual_level=item.residual_level,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@router.post("/threats", response_model=CatalogResponse, status_code=201)
async def create_threat(
    payload: CatalogCreate,
    principal: Principal = Depends(require_permission(Permission.RISK_WRITE)),
    db: AsyncSession = Depends(get_db),
) -> CatalogResponse:
    item = Threat(
        organization_id=_org(principal),
        created_by=principal.user.id,
        name=payload.name,
        description=payload.description,
        likelihood=payload.rating,
    )
    db.add(item)
    await db.commit()
    return CatalogResponse(
        id=item.id, name=item.name, description=item.description, rating=item.likelihood
    )


@router.get("/threats", response_model=list[CatalogResponse])
async def list_threats(
    principal: Principal = Depends(require_permission(Permission.RISK_READ)),
    db: AsyncSession = Depends(get_db),
) -> list[CatalogResponse]:
    items = (
        await db.scalars(
            select(Threat)
            .where(Threat.organization_id == _org(principal), Threat.deleted_at.is_(None))
            .order_by(Threat.name)
        )
    ).all()
    return [
        CatalogResponse(
            id=item.id, name=item.name, description=item.description, rating=item.likelihood
        )
        for item in items
    ]


@router.post("/vulnerabilities", response_model=CatalogResponse, status_code=201)
async def create_vulnerability(
    payload: CatalogCreate,
    principal: Principal = Depends(require_permission(Permission.RISK_WRITE)),
    db: AsyncSession = Depends(get_db),
) -> CatalogResponse:
    item = Vulnerability(
        organization_id=_org(principal),
        created_by=principal.user.id,
        name=payload.name,
        description=payload.description,
        severity=payload.rating,
    )
    db.add(item)
    await db.commit()
    return CatalogResponse(
        id=item.id, name=item.name, description=item.description, rating=item.severity
    )


@router.get("/vulnerabilities", response_model=list[CatalogResponse])
async def list_vulnerabilities(
    principal: Principal = Depends(require_permission(Permission.RISK_READ)),
    db: AsyncSession = Depends(get_db),
) -> list[CatalogResponse]:
    items = (
        await db.scalars(
            select(Vulnerability)
            .where(
                Vulnerability.organization_id == _org(principal), Vulnerability.deleted_at.is_(None)
            )
            .order_by(Vulnerability.name)
        )
    ).all()
    return [
        CatalogResponse(
            id=item.id, name=item.name, description=item.description, rating=item.severity
        )
        for item in items
    ]


@router.get("/risks", response_model=RiskPage)
async def list_risks(
    search: str | None = Query(default=None, max_length=100),
    level: RiskLevel | None = None,
    risk_status: RiskStatus | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    principal: Principal = Depends(require_permission(Permission.RISK_READ)),
    db: AsyncSession = Depends(get_db),
) -> RiskPage:
    organization_id = _org(principal)
    filters = [Risk.organization_id == organization_id, Risk.deleted_at.is_(None)]
    if search:
        filters.append(or_(Risk.title.ilike(f"%{search}%"), Risk.code.ilike(f"%{search}%")))
    if level:
        filters.append(Risk.inherent_level == level)
    if risk_status:
        filters.append(Risk.status == risk_status)
    total = await db.scalar(select(func.count(Risk.id)).where(*filters)) or 0
    items = (
        await db.scalars(
            select(Risk)
            .where(*filters)
            .order_by(Risk.inherent_score.desc(), Risk.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    return RiskPage(
        items=[_response(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=ceil(total / page_size) if total else 0,
    )


async def _get_risk(db: AsyncSession, risk_id: UUID, organization_id: UUID) -> Risk:
    item = await db.scalar(
        select(Risk)
        .options(selectinload(Risk.treatments))
        .where(
            Risk.id == risk_id, Risk.organization_id == organization_id, Risk.deleted_at.is_(None)
        )
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Riesgo no encontrado")
    return item


@router.get("/risks/{risk_id}", response_model=RiskResponse)
async def get_risk(
    risk_id: UUID,
    principal: Principal = Depends(require_permission(Permission.RISK_READ)),
    db: AsyncSession = Depends(get_db),
) -> RiskResponse:
    return _response(await _get_risk(db, risk_id, _org(principal)))


async def _apply(payload: RiskCreate, item: Risk, bands: tuple[RiskBand, ...]) -> None:
    for key, value in payload.model_dump().items():
        setattr(item, key, value)
    item.inherent_score, item.inherent_level = calculate_risk(
        payload.probability, payload.impact, bands
    )
    item.residual_score, item.residual_level = calculate_risk(
        payload.residual_probability, payload.residual_impact, bands
    )


@router.post("/risks", response_model=RiskResponse, status_code=201)
async def create_risk(
    payload: RiskCreate,
    request: Request,
    principal: Principal = Depends(require_permission(Permission.RISK_WRITE)),
    db: AsyncSession = Depends(get_db),
) -> RiskResponse:
    organization_id = _org(principal)
    await _validate_relations(db, payload, organization_id)
    if await db.scalar(
        select(Risk.id).where(
            Risk.organization_id == organization_id,
            Risk.code == payload.code,
            Risk.deleted_at.is_(None),
        )
    ):
        raise HTTPException(status_code=409, detail="El código de riesgo ya existe")
    item = Risk(
        organization_id=organization_id,
        created_by=principal.user.id,
        inherent_score=1,
        inherent_level=RiskLevel.LOW,
        residual_score=1,
        residual_level=RiskLevel.LOW,
        **payload.model_dump(),
    )
    await _apply(payload, item, await _bands(db, organization_id))
    db.add(item)
    await db.flush()
    add_audit(
        db,
        request,
        "risk.create",
        "risk",
        "success",
        user_id=principal.user.id,
        organization_id=organization_id,
        resource_id=str(item.id),
        changes={"score": item.inherent_score, "level": item.inherent_level},
    )
    await db.commit()
    return _response(item)


@router.put("/risks/{risk_id}", response_model=RiskResponse)
async def update_risk(
    risk_id: UUID,
    payload: RiskUpdate,
    request: Request,
    principal: Principal = Depends(require_permission(Permission.RISK_WRITE)),
    db: AsyncSession = Depends(get_db),
) -> RiskResponse:
    organization_id = _org(principal)
    item = await _get_risk(db, risk_id, organization_id)
    await _validate_relations(db, payload, organization_id)
    previous = {"inherent_score": item.inherent_score, "residual_score": item.residual_score}
    await _apply(payload, item, await _bands(db, organization_id))
    add_audit(
        db,
        request,
        "risk.update",
        "risk",
        "success",
        user_id=principal.user.id,
        organization_id=organization_id,
        resource_id=str(item.id),
        changes={
            "previous": previous,
            "new": {"inherent_score": item.inherent_score, "residual_score": item.residual_score},
        },
    )
    await db.commit()
    return _response(item)


@router.delete("/risks/{risk_id}", status_code=204)
async def delete_risk(
    risk_id: UUID,
    request: Request,
    principal: Principal = Depends(require_permission(Permission.RISK_DELETE)),
    db: AsyncSession = Depends(get_db),
) -> None:
    organization_id = _org(principal)
    item = await _get_risk(db, risk_id, organization_id)
    item.deleted_at = utc_now()
    add_audit(
        db,
        request,
        "risk.delete",
        "risk",
        "success",
        user_id=principal.user.id,
        organization_id=organization_id,
        resource_id=str(item.id),
    )
    await db.commit()


@router.post("/risks/{risk_id}/treatments", response_model=TreatmentResponse, status_code=201)
async def add_treatment(
    risk_id: UUID,
    payload: TreatmentCreate,
    request: Request,
    principal: Principal = Depends(require_permission(Permission.RISK_WRITE)),
    db: AsyncSession = Depends(get_db),
) -> RiskTreatment:
    organization_id = _org(principal)
    item = await _get_risk(db, risk_id, organization_id)
    treatment = RiskTreatment(
        organization_id=organization_id,
        risk_id=item.id,
        created_by=principal.user.id,
        **payload.model_dump(),
    )
    db.add(treatment)
    item.progress = payload.progress
    item.status = RiskStatus.IN_TREATMENT
    add_audit(
        db,
        request,
        "risk.treatment.create",
        "risk_treatment",
        "success",
        user_id=principal.user.id,
        organization_id=organization_id,
        resource_id=str(treatment.id),
    )
    await db.commit()
    return treatment


@router.get("/risks/{risk_id}/treatments", response_model=list[TreatmentResponse])
async def list_treatments(
    risk_id: UUID,
    principal: Principal = Depends(require_permission(Permission.RISK_READ)),
    db: AsyncSession = Depends(get_db),
) -> list[RiskTreatment]:
    item = await _get_risk(db, risk_id, _org(principal))
    return [t for t in item.treatments if t.deleted_at is None]


@router.put("/settings/risk-bands", status_code=status.HTTP_204_NO_CONTENT)
async def update_risk_bands(
    payload: RiskBandsUpdate,
    request: Request,
    principal: Principal = Depends(require_permission(Permission.RISK_SETTINGS)),
    db: AsyncSession = Depends(get_db),
) -> None:
    organization_id = _org(principal)
    value: dict[str, object] = {"bands": payload.bands}
    bands_from_setting(value)
    setting = await db.scalar(
        select(SystemSetting).where(
            SystemSetting.organization_id == organization_id,
            SystemSetting.key == "risk_matrix_thresholds",
        )
    )
    if setting is None:
        setting = SystemSetting(
            organization_id=organization_id,
            key="risk_matrix_thresholds",
            value=value,
            updated_by=principal.user.id,
        )
        db.add(setting)
    else:
        setting.value = value
        setting.updated_by = principal.user.id
    add_audit(
        db,
        request,
        "risk.settings.update",
        "system_setting",
        "success",
        user_id=principal.user.id,
        organization_id=organization_id,
        changes=value,
    )
    await db.commit()


@router.get("/settings/risk-bands", response_model=RiskBandsUpdate)
async def read_risk_bands(
    principal: Principal = Depends(require_permission(Permission.RISK_READ)),
    db: AsyncSession = Depends(get_db),
) -> RiskBandsUpdate:
    bands = await _bands(db, _org(principal))
    return RiskBandsUpdate(bands=[
        {"level": band.level.value, "minimum": band.minimum, "maximum": band.maximum}
        for band in bands
    ])
