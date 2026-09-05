import asyncio
import hashlib
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

from sqlalchemy import or_, update
from sqlalchemy.sql.elements import ColumnElement

from app.core.config import settings
from app.core.database import SessionFactory, dispose_engine
from app.models.reports import Report, ReportStatus
from app.services.pdf_reports import build_pdf
from app.services.report_data import collect_report_data
from app.worker import celery_app

logger = logging.getLogger(__name__)
background_report_lock = asyncio.Lock()


async def generate_in_background(report_id: UUID) -> None:
    # Share the API event loop and generate one PDF at a time on small instances.
    async with background_report_lock:
        await _generate(report_id)


def recoverable_reports() -> ColumnElement[bool]:
    return or_(
        Report.status == ReportStatus.PENDING,
        (Report.status == ReportStatus.PROCESSING)
        & (Report.updated_at < datetime.now(UTC) - timedelta(minutes=10)),
    )


async def _generate(report_id: UUID) -> None:
    async with SessionFactory() as db:
        claimed = await db.execute(
            update(Report)
            .where(Report.id == report_id, recoverable_reports())
            .values(status=ReportStatus.PROCESSING, updated_at=datetime.now(UTC))
            .returning(Report.id)
        )
        if claimed.scalar_one_or_none() is None:
            await db.rollback()
            return
        await db.commit()
        report = await db.get(Report, report_id)
        if report is None:
            return
        try:
            data = await collect_report_data(db, report)
            storage_key = f"{report.organization_id}/{report.id}.pdf"
            path = Path(settings.report_storage_path).resolve() / storage_key
            await asyncio.to_thread(build_pdf, path, str(report.report_type), data)
            content = path.read_bytes()
            report.pdf_content = content
            report.storage_key = storage_key
            report.file_name = f"{report.report_type}-{report.id}.pdf"
            report.content_type = "application/pdf"
            report.size_bytes = len(content)
            report.sha256 = hashlib.sha256(content).hexdigest()
            report.status = ReportStatus.COMPLETED
            report.error_message = None
        except Exception:
            logger.exception("PDF generation failed for report %s", report_id)
            await db.rollback()
            report = await db.get(Report, report_id)
            if report is None:
                return
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
