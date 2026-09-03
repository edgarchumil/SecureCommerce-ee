from math import ceil
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.assets import Asset, AssetDependency, AssetStatus, AssetType
from app.models.base import utc_now
from app.schemas.assets import AssetCreate, AssetPage, AssetResponse, AssetUpdate
from app.security.dependencies import Principal, require_permission
from app.security.permissions import Permission
from app.services.audit import add_audit

router = APIRouter(prefix="/assets", tags=["activos"])


def _organization_id(principal: Principal) -> UUID:
    if principal.organization_id is None:
        raise HTTPException(status_code=403, detail="Seleccione una organización")
    return principal.organization_id


def _asset_response(asset: Asset) -> AssetResponse:
    return AssetResponse(
        id=asset.id,
        organization_id=asset.organization_id,
        name=asset.name,
        internal_code=asset.internal_code,
        asset_type=asset.asset_type,
        description=asset.description,
        owner=asset.owner,
        technical_owner=asset.technical_owner,
        location=asset.location,
        ip_address=asset.ip_address,
        operating_system=asset.operating_system,
        manufacturer=asset.manufacturer,
        model=asset.model,
        exposure_level=asset.exposure_level,
        status=asset.status,
        acquisition_date=asset.acquisition_date,
        confidentiality_criticality=asset.confidentiality_criticality,
        integrity_criticality=asset.integrity_criticality,
        availability_criticality=asset.availability_criticality,
        overall_criticality=asset.overall_criticality,
        tags=asset.tags,
        notes=asset.notes,
        dependency_ids=[item.depends_on_asset_id for item in asset.outgoing_dependencies],
        created_at=asset.created_at,
        updated_at=asset.updated_at,
    )


async def _get_asset(db: AsyncSession, asset_id: UUID, organization_id: UUID) -> Asset:
    asset = await db.scalar(
        select(Asset)
        .options(selectinload(Asset.outgoing_dependencies))
        .where(
            Asset.id == asset_id,
            Asset.organization_id == organization_id,
            Asset.deleted_at.is_(None),
        )
    )
    if asset is None:
        raise HTTPException(status_code=404, detail="Activo no encontrado")
    return asset


async def _validate_dependencies(
    db: AsyncSession,
    dependency_ids: list[UUID],
    organization_id: UUID,
    asset_id: UUID | None = None,
) -> list[UUID]:
    unique_ids = list(dict.fromkeys(dependency_ids))
    if asset_id is not None and asset_id in unique_ids:
        raise HTTPException(status_code=422, detail="Un activo no puede depender de sí mismo")
    if not unique_ids:
        return []
    found = set(
        (
            await db.scalars(
                select(Asset.id).where(
                    Asset.id.in_(unique_ids),
                    Asset.organization_id == organization_id,
                    Asset.deleted_at.is_(None),
                )
            )
        ).all()
    )
    if found != set(unique_ids):
        raise HTTPException(status_code=422, detail="Una o más dependencias no son válidas")
    return unique_ids


@router.get("", response_model=AssetPage)
async def list_assets(
    search: str | None = Query(default=None, max_length=100),
    asset_type: AssetType | None = None,
    asset_status: AssetStatus | None = Query(default=None, alias="status"),
    criticality: int | None = Query(default=None, ge=1, le=5),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort_by: str = Query(
        default="name",
        pattern=r"^(name|internal_code|asset_type|status|overall_criticality|created_at)$",
    ),
    sort_order: str = Query(default="asc", pattern=r"^(asc|desc)$"),
    principal: Principal = Depends(require_permission(Permission.ASSET_READ)),
    db: AsyncSession = Depends(get_db),
) -> AssetPage:
    organization_id = _organization_id(principal)
    filters = [Asset.organization_id == organization_id, Asset.deleted_at.is_(None)]
    if search:
        term = f"%{search.strip()}%"
        filters.append(or_(Asset.name.ilike(term), Asset.internal_code.ilike(term)))
    if asset_type:
        filters.append(Asset.asset_type == asset_type)
    if asset_status:
        filters.append(Asset.status == asset_status)
    if criticality:
        filters.append(Asset.overall_criticality == criticality)
    total = await db.scalar(select(func.count(Asset.id)).where(*filters)) or 0
    sort_column = getattr(Asset, sort_by)
    order = desc(sort_column) if sort_order == "desc" else asc(sort_column)
    items = (
        await db.scalars(
            select(Asset)
            .options(selectinload(Asset.outgoing_dependencies))
            .where(*filters)
            .order_by(order, Asset.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    return AssetPage(
        items=[_asset_response(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=ceil(total / page_size) if total else 0,
    )


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: UUID,
    principal: Principal = Depends(require_permission(Permission.ASSET_READ)),
    db: AsyncSession = Depends(get_db),
) -> AssetResponse:
    return _asset_response(await _get_asset(db, asset_id, _organization_id(principal)))


@router.post("", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
async def create_asset(
    payload: AssetCreate,
    request: Request,
    principal: Principal = Depends(require_permission(Permission.ASSET_CREATE)),
    db: AsyncSession = Depends(get_db),
) -> AssetResponse:
    organization_id = _organization_id(principal)
    duplicate = await db.scalar(
        select(Asset.id).where(
            Asset.organization_id == organization_id,
            Asset.internal_code == payload.internal_code,
            Asset.deleted_at.is_(None),
        )
    )
    if duplicate:
        raise HTTPException(status_code=409, detail="El código interno ya está en uso")
    dependency_ids = await _validate_dependencies(db, payload.dependency_ids, organization_id)
    values = payload.model_dump(exclude={"dependency_ids"})
    asset = Asset(
        **values,
        organization_id=organization_id,
        created_by=principal.user.id,
        outgoing_dependencies=[],
        overall_criticality=max(
            payload.confidentiality_criticality,
            payload.integrity_criticality,
            payload.availability_criticality,
        ),
    )
    db.add(asset)
    await db.flush()
    asset.outgoing_dependencies.extend(
        AssetDependency(
            organization_id=organization_id,
            asset_id=asset.id,
            depends_on_asset_id=dependency_id,
        )
        for dependency_id in dependency_ids
    )
    add_audit(
        db,
        request,
        "asset.create",
        "asset",
        "success",
        user_id=principal.user.id,
        organization_id=organization_id,
        resource_id=str(asset.id),
        changes={"name": asset.name, "internal_code": asset.internal_code},
    )
    await db.commit()
    await db.refresh(asset, attribute_names=["outgoing_dependencies"])
    return _asset_response(asset)


@router.put("/{asset_id}", response_model=AssetResponse)
async def update_asset(
    asset_id: UUID,
    payload: AssetUpdate,
    request: Request,
    principal: Principal = Depends(require_permission(Permission.ASSET_UPDATE)),
    db: AsyncSession = Depends(get_db),
) -> AssetResponse:
    organization_id = _organization_id(principal)
    asset = await _get_asset(db, asset_id, organization_id)
    duplicate = await db.scalar(
        select(Asset.id).where(
            Asset.organization_id == organization_id,
            Asset.internal_code == payload.internal_code,
            Asset.id != asset.id,
            Asset.deleted_at.is_(None),
        )
    )
    if duplicate:
        raise HTTPException(status_code=409, detail="El código interno ya está en uso")
    dependency_ids = await _validate_dependencies(
        db, payload.dependency_ids, organization_id, asset.id
    )
    previous = {"name": asset.name, "internal_code": asset.internal_code}
    for field, value in payload.model_dump(exclude={"dependency_ids"}).items():
        setattr(asset, field, value)
    asset.overall_criticality = max(
        payload.confidentiality_criticality,
        payload.integrity_criticality,
        payload.availability_criticality,
    )
    asset.outgoing_dependencies.clear()
    asset.outgoing_dependencies.extend(
        AssetDependency(
            organization_id=organization_id,
            asset_id=asset.id,
            depends_on_asset_id=dependency_id,
        )
        for dependency_id in dependency_ids
    )
    add_audit(
        db,
        request,
        "asset.update",
        "asset",
        "success",
        user_id=principal.user.id,
        organization_id=organization_id,
        resource_id=str(asset.id),
        changes={
            "previous": previous,
            "new": {"name": asset.name, "internal_code": asset.internal_code},
        },
    )
    await db.commit()
    return _asset_response(asset)


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset(
    asset_id: UUID,
    request: Request,
    principal: Principal = Depends(require_permission(Permission.ASSET_DELETE)),
    db: AsyncSession = Depends(get_db),
) -> None:
    organization_id = _organization_id(principal)
    asset = await _get_asset(db, asset_id, organization_id)
    asset.deleted_at = utc_now()
    add_audit(
        db,
        request,
        "asset.delete",
        "asset",
        "success",
        user_id=principal.user.id,
        organization_id=organization_id,
        resource_id=str(asset.id),
    )
    await db.commit()
