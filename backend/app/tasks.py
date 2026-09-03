import asyncio
import hashlib
from pathlib import Path
from uuid import UUID

from sqlalchemy import func, select

from app.core.config import settings
from app.core.database import SessionFactory
from app.models.assets import Asset
from app.models.evaluations import Answer
from app.models.identity import Organization
from app.models.reports import Report, ReportStatus
from app.models.risks import Risk
from app.services.pdf_reports import build_pdf
from app.worker import celery_app


async def _generate(report_id: UUID) -> None:
    async with SessionFactory() as db:
        report = await db.get(Report, report_id)
        if report is None:
            return
        report.status = ReportStatus.PROCESSING
        await db.commit()
        try:
            organization = await db.get(Organization, report.organization_id)
            assets = (
                await db.scalars(
                    select(Asset).where(
                        Asset.organization_id == report.organization_id, Asset.deleted_at.is_(None)
                    )
                )
            ).all()
            risks = (
                await db.scalars(
                    select(Risk)
                    .where(
                        Risk.organization_id == report.organization_id, Risk.deleted_at.is_(None)
                    )
                    .order_by(Risk.inherent_score.desc())
                    .limit(10)
                )
            ).all()
            maturity = await db.scalar(
                select(func.avg(Answer.maturity)).where(
                    Answer.organization_id == report.organization_id
                )
            )
            data: dict[str, object] = {
                "title": report.title,
                "organization": organization.name if organization else "Organización",
                "scope": report.scope,
                "summary": "Panorama de activos, madurez y riesgos registrado en la plataforma.",
                "metrics": [
                    {"label": "Activos", "value": len(assets)},
                    {"label": "Riesgos", "value": len(risks)},
                    {
                        "label": "Madurez NIST",
                        "value": f"{round(float(maturity or 0) / 4 * 100, 1)}%",
                    },
                ],
                "risks": [
                    {
                        "code": item.code,
                        "title": item.title,
                        "level": str(item.inherent_level),
                        "score": item.inherent_score,
                        "strategy": str(item.treatment_strategy),
                    }
                    for item in risks
                ],
                "assets": [
                    {
                        "code": item.internal_code,
                        "name": item.name,
                        "type": str(item.asset_type),
                        "criticality": item.overall_criticality,
                    }
                    for item in assets
                ],
            }
            storage_key = f"{report.organization_id}/{report.id}.pdf"
            path = Path(settings.report_storage_path).resolve() / storage_key
            build_pdf(path, str(report.report_type), data)
            content = path.read_bytes()
            report.storage_key = storage_key
            report.file_name = f"{report.report_type}-{report.id}.pdf"
            report.content_type = "application/pdf"
            report.size_bytes = len(content)
            report.sha256 = hashlib.sha256(content).hexdigest()
            report.status = ReportStatus.COMPLETED
            report.error_message = None
        except Exception:
            report.status = ReportStatus.FAILED
            report.error_message = "No fue posible generar el reporte"
        await db.commit()


@celery_app.task(name="reports.generate")  # type: ignore[untyped-decorator]
def generate_report(report_id: str) -> None:
    asyncio.run(_generate(UUID(report_id)))
