from pathlib import Path
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.reports import Report, ReportStatus
from app.schemas.reports import ReportCreate, ReportResponse
from app.security.dependencies import Principal, require_permission
from app.security.permissions import Permission
from app.services.audit import add_audit
from app.tasks import generate_in_background, generate_report, recoverable_reports

router = APIRouter(prefix="/reports", tags=["reportes"])


def _org(principal: Principal) -> UUID:
    if principal.organization_id is None:
        raise HTTPException(status_code=403, detail="Seleccione una organización")
    return principal.organization_id


def _response(item: Report) -> ReportResponse:
    return ReportResponse(
        id=item.id,
        report_type=item.report_type,
        status=item.status,
        title=item.title,
        scope=item.scope,
        file_name=item.file_name,
        size_bytes=item.size_bytes,
        sha256=item.sha256,
        error_message=item.error_message,
        created_at=item.created_at,
        updated_at=item.updated_at,
        download_url=f"/api/v1/reports/{item.id}/download"
        if item.status == ReportStatus.COMPLETED
        else None,
    )


@router.post("", response_model=ReportResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_report(
    payload: ReportCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    principal: Principal = Depends(require_permission(Permission.REPORT_CREATE)),
    db: AsyncSession = Depends(get_db),
) -> ReportResponse:
    organization_id = _org(principal)
    item = Report(
        organization_id=organization_id, created_by=principal.user.id, **payload.model_dump()
    )
    db.add(item)
    await db.flush()
    add_audit(
        db,
        request,
        "report.create",
        "report",
        "success",
        user_id=principal.user.id,
        organization_id=organization_id,
        resource_id=str(item.id),
        changes={"type": payload.report_type.value},
    )
    await db.commit()
    if settings.report_execution_mode == "background":
        background_tasks.add_task(generate_in_background, item.id)
    else:
        generate_report.delay(str(item.id))
    return _response(item)


@router.get("", response_model=list[ReportResponse])
async def list_reports(
    background_tasks: BackgroundTasks,
    principal: Principal = Depends(require_permission(Permission.REPORT_READ)),
    db: AsyncSession = Depends(get_db),
) -> list[ReportResponse]:
    items = (
        await db.scalars(
            select(Report)
            .where(Report.organization_id == _org(principal))
            .order_by(Report.created_at.desc())
        )
    ).all()
    if settings.report_execution_mode == "background":
        pending = (
            await db.scalars(
                select(Report.id)
                .where(Report.organization_id == _org(principal), recoverable_reports())
                .order_by(Report.created_at)
                .limit(3)
            )
        ).all()
        for report_id in pending:
            background_tasks.add_task(generate_in_background, report_id)
    return [_response(item) for item in items]


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: UUID,
    principal: Principal = Depends(require_permission(Permission.REPORT_READ)),
    db: AsyncSession = Depends(get_db),
) -> ReportResponse:
    item = await db.scalar(
        select(Report).where(Report.id == report_id, Report.organization_id == _org(principal))
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    return _response(item)


@router.get("/{report_id}/download", response_class=FileResponse)
async def download_report(
    report_id: UUID,
    request: Request,
    principal: Principal = Depends(require_permission(Permission.REPORT_READ)),
    db: AsyncSession = Depends(get_db),
) -> Response:
    organization_id = _org(principal)
    item = await db.scalar(
        select(Report).where(
            Report.id == report_id,
            Report.organization_id == organization_id,
            Report.status == ReportStatus.COMPLETED,
        )
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Reporte no disponible")
    content = await db.scalar(
        select(Report.pdf_content).where(
            Report.id == item.id,
            Report.organization_id == organization_id,
        )
    )
    root = Path(settings.report_storage_path).resolve()
    path = (root / (item.storage_key or "")).resolve()
    if content is None and (root not in path.parents or not path.is_file()):
        raise HTTPException(status_code=404, detail="Reporte no disponible")
    add_audit(
        db,
        request,
        "report.download",
        "report",
        "success",
        user_id=principal.user.id,
        organization_id=organization_id,
        resource_id=str(item.id),
    )
    await db.commit()
    if content is not None:
        filename = quote(item.file_name or f"reporte-{item.id}.pdf")
        return Response(
            content=content,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"},
        )
    return FileResponse(path, media_type="application/pdf", filename=item.file_name)
