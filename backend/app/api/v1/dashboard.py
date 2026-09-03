from collections import Counter
from datetime import UTC, date, datetime, time
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from app.core.database import get_db
from app.models.assets import Asset, AssetType
from app.models.evaluations import Answer, Evaluation
from app.models.risks import Risk
from app.schemas.dashboard import ChartPoint, DashboardFilters, DashboardResponse, Metric
from app.security.dependencies import Principal, require_permission
from app.security.permissions import Permission

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _org(principal: Principal) -> UUID:
    if principal.organization_id is None:
        raise HTTPException(status_code=403, detail="Seleccione una organización")
    return principal.organization_id


def _range(date_from: date | None, date_to: date | None) -> tuple[datetime | None, datetime | None]:
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=422, detail="El rango de fechas no es válido")
    start = datetime.combine(date_from, time.min, UTC) if date_from else None
    end = datetime.combine(date_to, time.max, UTC) if date_to else None
    return start, end


def _dates(
    model: type[Any],
    start: datetime | None,
    end: datetime | None,
) -> list[ColumnElement[bool]]:
    result: list[ColumnElement[bool]] = []
    if start:
        result.append(model.created_at >= start)
    if end:
        result.append(model.created_at <= end)
    return result


@router.get("", response_model=DashboardResponse)
async def dashboard(
    date_from: date | None = None,
    date_to: date | None = None,
    asset_type: AssetType | None = Query(default=None),
    principal: Principal = Depends(require_permission(Permission.DASHBOARD_READ)),
    db: AsyncSession = Depends(get_db),
) -> DashboardResponse:
    organization_id = _org(principal)
    start, end = _range(date_from, date_to)
    asset_filters = [
        Asset.organization_id == organization_id,
        Asset.deleted_at.is_(None),
        *_dates(Asset, start, end),
    ]
    if asset_type:
        asset_filters.append(Asset.asset_type == asset_type)
    risk_filters = [
        Risk.organization_id == organization_id,
        Risk.deleted_at.is_(None),
        *_dates(Risk, start, end),
    ]
    if asset_type:
        risk_filters.append(Risk.asset_id.in_(select(Asset.id).where(*asset_filters)))
    evaluation_filters = [
        Evaluation.organization_id == organization_id,
        Evaluation.deleted_at.is_(None),
        *_dates(Evaluation, start, end),
    ]

    asset_rows = (
        await db.execute(
            select(Asset.asset_type, func.count()).where(*asset_filters).group_by(Asset.asset_type)
        )
    ).all()
    risk_rows = (
        await db.execute(
            select(Risk.inherent_level, func.count())
            .where(*risk_filters)
            .group_by(Risk.inherent_level)
        )
    ).all()
    evaluation_rows = (
        await db.execute(
            select(Evaluation.status, func.count())
            .where(*evaluation_filters)
            .group_by(Evaluation.status)
        )
    ).all()
    risk_dates = (await db.scalars(select(Risk.created_at).where(*risk_filters))).all()
    risk_time_rows = sorted(Counter(item.strftime("%Y-%m") for item in risk_dates).items())
    maturity = await db.scalar(
        select(func.avg(Answer.maturity))
        .join(Evaluation, Answer.evaluation_id == Evaluation.id)
        .where(Answer.organization_id == organization_id, *evaluation_filters)
    )
    progress = await db.scalar(select(func.avg(Risk.progress)).where(*risk_filters))
    return DashboardResponse(
        filters=DashboardFilters(date_from=date_from, date_to=date_to, asset_type=asset_type),
        kpis=[
            Metric(key="assets", label="Activos", value=sum(count for _, count in asset_rows)),
            Metric(
                key="maturity",
                label="Madurez NIST",
                value=round(float(maturity or 0) / 4 * 100, 1),
                unit="%",
            ),
            Metric(
                key="risks", label="Riesgos abiertos", value=sum(count for _, count in risk_rows)
            ),
            Metric(
                key="priority_risks",
                label="Riesgos prioritarios",
                value=sum(
                    count for level, count in risk_rows if str(level) in {"high", "critical"}
                ),
            ),
            Metric(
                key="treatment_progress",
                label="Avance de tratamiento",
                value=round(float(progress or 0), 1),
                unit="%",
            ),
        ],
        assets_by_type=[
            ChartPoint(key=str(key), label=str(key).replace("_", " ").title(), value=value)
            for key, value in asset_rows
        ],
        risks_by_level=[
            ChartPoint(key=str(key), label=str(key).title(), value=value)
            for key, value in risk_rows
        ],
        evaluations_by_status=[
            ChartPoint(key=str(key), label=str(key).replace("_", " ").title(), value=value)
            for key, value in evaluation_rows
        ],
        risks_over_time=[
            ChartPoint(key=key, label=key, value=value) for key, value in risk_time_rows
        ],
    )
