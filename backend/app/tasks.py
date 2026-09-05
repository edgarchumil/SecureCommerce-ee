import asyncio
import hashlib
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from sqlalchemy import func, select

from app.core.config import settings
from app.core.database import SessionFactory
from app.models.assets import Asset
from app.models.evaluations import (
    Answer,
    Evidence,
    FrameworkCategory,
    FrameworkControl,
    FrameworkFunction,
    Question,
)
from app.models.identity import Organization, User
from app.models.reports import Report, ReportStatus
from app.models.risks import Risk, RiskTreatment
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
                )
            ).all()
            maturity = await db.scalar(
                select(func.avg(Answer.maturity)).where(
                    Answer.organization_id == report.organization_id
                )
            )
            maturity_rows = (
                await db.execute(
                    select(
                        FrameworkFunction.code,
                        FrameworkFunction.name,
                        func.avg(Answer.maturity),
                        func.count(Answer.id),
                    )
                    .join(FrameworkCategory, FrameworkCategory.function_id == FrameworkFunction.id)
                    .join(FrameworkControl, FrameworkControl.category_id == FrameworkCategory.id)
                    .join(Question, Question.control_id == FrameworkControl.id)
                    .join(Answer, Answer.question_id == Question.id)
                    .where(Answer.organization_id == report.organization_id)
                    .group_by(
                        FrameworkFunction.id,
                        FrameworkFunction.code,
                        FrameworkFunction.name,
                        FrameworkFunction.sort_order,
                    )
                    .order_by(FrameworkFunction.sort_order)
                )
            ).all()
            treatments = (
                await db.scalars(
                    select(RiskTreatment).where(
                        RiskTreatment.organization_id == report.organization_id,
                        RiskTreatment.deleted_at.is_(None),
                    )
                )
            ).all()
            evidence_count = int(
                await db.scalar(
                    select(func.count(Evidence.id)).where(
                        Evidence.organization_id == report.organization_id,
                        Evidence.deleted_at.is_(None),
                    )
                )
                or 0
            )
            user_ids = {report.created_by}
            user_ids.update(item.responsible_user_id for item in risks if item.responsible_user_id)
            user_ids.update(
                item.responsible_user_id for item in treatments if item.responsible_user_id
            )
            users = (await db.scalars(select(User).where(User.id.in_(user_ids)))).all()
            user_names = {item.id: item.full_name for item in users}
            risk_distribution = {level: 0 for level in ("critical", "high", "medium", "low")}
            for risk in risks:
                level = str(risk.inherent_level).split(".")[-1].lower()
                if level in risk_distribution:
                    risk_distribution[level] += 1
            maturity_percent = round(float(maturity or 0) / 4 * 100, 1)
            data: dict[str, object] = {
                "title": report.title,
                "organization": organization.name if organization else "Organización",
                "company": {
                    "slug": organization.slug if organization else None,
                    "sector": organization.sector if organization else None,
                    "size": organization.size if organization else None,
                    "country": organization.country if organization else None,
                    "is_active": organization.is_active if organization else None,
                },
                "scope": report.scope,
                "report_id": str(report.id),
                "generated_at": datetime.now(UTC),
                "prepared_by": user_names.get(report.created_by, "SecureCommerce Advisor"),
                "summary": "Panorama de activos, madurez y riesgos registrado en la plataforma.",
                "asset_count": len(assets),
                "risk_count": len(risks),
                "answered_controls": sum(int(row[3]) for row in maturity_rows),
                "evidence_count": evidence_count,
                "maturity_percent": maturity_percent,
                "metrics": [
                    {"label": "Activos registrados", "value": len(assets)},
                    {"label": "Riesgos identificados", "value": len(risks)},
                    {
                        "label": "Madurez NIST CSF 2.0",
                        "value": f"{maturity_percent}%",
                    },
                    {"label": "Evidencias", "value": evidence_count},
                ],
                "risk_distribution": risk_distribution,
                "maturity_functions": [
                    {
                        "code": row[0],
                        "name": row[1],
                        "percent": round(float(row[2] or 0) / 4 * 100, 1),
                        "answers": int(row[3]),
                    }
                    for row in maturity_rows
                ],
                "risks": [
                    {
                        "code": item.code,
                        "title": item.title,
                        "level": str(item.inherent_level),
                        "score": item.inherent_score,
                        "strategy": str(item.treatment_strategy),
                        "description": item.description,
                        "probability": item.probability,
                        "impact": item.impact,
                        "residual_probability": item.residual_probability,
                        "residual_impact": item.residual_impact,
                        "residual_score": item.residual_score,
                        "residual_level": str(item.residual_level),
                        "status": str(item.status),
                        "progress": item.progress,
                        "target_date": item.target_date.isoformat() if item.target_date else None,
                        "responsible": user_names.get(item.responsible_user_id, "No asignado"),
                        "controls": item.existing_controls,
                    }
                    for item in risks[:10]
                ],
                "assets": [
                    {
                        "code": item.internal_code,
                        "name": item.name,
                        "type": str(item.asset_type),
                        "criticality": item.overall_criticality,
                        "owner": item.owner,
                        "technical_owner": item.technical_owner,
                        "location": item.location,
                        "exposure": str(item.exposure_level),
                        "status": str(item.status),
                    }
                    for item in assets
                ],
                "recommendations": [
                    {
                        "action": item.action,
                        "responsible": user_names.get(item.responsible_user_id, "No asignado"),
                        "target_date": item.target_date.isoformat()
                        if item.target_date
                        else "No definida",
                        "progress": item.progress,
                    }
                    for item in sorted(
                        treatments, key=lambda value: (value.target_date is None, value.target_date)
                    )
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
