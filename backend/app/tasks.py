import asyncio
import hashlib
from pathlib import Path
from uuid import UUID

from app.core.config import settings
from app.core.database import SessionFactory, dispose_engine
from app.models.reports import Report, ReportStatus
from app.services.pdf_reports import build_pdf
from app.services.report_data import collect_report_data
from app.worker import celery_app


async def _generate(report_id: UUID) -> None:
    async with SessionFactory() as db:
        report = await db.get(Report, report_id)
        if report is None:
            return
        report.status = ReportStatus.PROCESSING
        await db.commit()
        try:
            data = await collect_report_data(db, report)
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
    async def run() -> None:
        try:
            await _generate(UUID(report_id))
        finally:
            # Each Celery invocation owns a new loop; never reuse its pooled connections.
            await dispose_engine()

    asyncio.run(run())
