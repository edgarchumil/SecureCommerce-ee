from collections import Counter
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assets import Asset
from app.models.evaluations import (
    Answer,
    Evaluation,
    Evidence,
    FrameworkCategory,
    FrameworkControl,
    FrameworkFunction,
    Question,
)
from app.models.identity import Membership, Organization, User
from app.models.operations import Incident
from app.models.reports import Report
from app.models.risks import Risk, RiskTreatment
from app.services.evaluation_scoring import ScoredAnswer, calculate_scores


async def collect_report_data(db: AsyncSession, report: Report) -> dict[str, Any]:
    org_id = report.organization_id
    organization = await db.get(Organization, org_id)
    creator = await db.get(User, report.created_by)
    assets = list(
        (
            await db.scalars(
                select(Asset)
                .where(
                    Asset.organization_id == org_id,
                    Asset.deleted_at.is_(None),
                )
                .order_by(Asset.overall_criticality.desc(), Asset.internal_code)
            )
        ).all()
    )
    risks = list(
        (
            await db.scalars(
                select(Risk)
                .where(
                    Risk.organization_id == org_id,
                    Risk.deleted_at.is_(None),
                )
                .order_by(Risk.inherent_score.desc(), Risk.code)
            )
        ).all()
    )
    treatments = list(
        (
            await db.scalars(
                select(RiskTreatment)
                .join(Risk)
                .where(
                    RiskTreatment.organization_id == org_id,
                    RiskTreatment.deleted_at.is_(None),
                    Risk.organization_id == org_id,
                    Risk.deleted_at.is_(None),
                )
                .order_by(
                    Risk.inherent_score.desc(),
                    RiskTreatment.target_date.asc().nulls_last(),
                    RiskTreatment.id,
                )
            )
        ).all()
    )
    users = {
        user.id: user.full_name
        for user in (
            await db.scalars(
                select(User)
                .join(Membership)
                .where(Membership.organization_id == org_id, User.deleted_at.is_(None)),
            )
        ).all()
    }
    incidents = list(
        (
            await db.scalars(
                select(Incident)
                .where(
                    Incident.organization_id == org_id,
                    Incident.deleted_at.is_(None),
                )
                .order_by(Incident.occurred_at.desc())
            )
        ).all()
    )
    evaluation = await db.scalar(
        select(Evaluation)
        .where(
            Evaluation.organization_id == org_id,
            Evaluation.deleted_at.is_(None),
        )
        .order_by(Evaluation.created_at.desc(), Evaluation.id.desc())
        .limit(1)
    )
    scores = None
    evidence_count = 0
    if evaluation:
        rows = (
            await db.execute(
                select(Question, FrameworkCategory, FrameworkFunction, Answer)
                .join(FrameworkControl, Question.control_id == FrameworkControl.id)
                .join(FrameworkCategory, FrameworkControl.category_id == FrameworkCategory.id)
                .join(FrameworkFunction, FrameworkCategory.function_id == FrameworkFunction.id)
                .outerjoin(
                    Answer,
                    (Answer.question_id == Question.id)
                    & (Answer.evaluation_id == evaluation.id)
                    & (Answer.organization_id == org_id),
                )
                .where(
                    FrameworkFunction.framework_id == evaluation.framework_id,
                    Question.is_active.is_(True),
                )
                .order_by(FrameworkFunction.sort_order, FrameworkCategory.sort_order)
            )
        ).all()
        scores = calculate_scores(
            [
                ScoredAnswer(
                    function.code,
                    function.name,
                    category.code,
                    category.name,
                    question.weight,
                    answer.maturity if answer else None,
                )
                for question, category, function, answer in rows
            ],
            evaluation.target_maturity,
        )
        evidence_count = (
            await db.scalar(
                select(func.count(Evidence.id))
                .join(Answer)
                .where(
                    Evidence.organization_id == org_id,
                    Evidence.deleted_at.is_(None),
                    Answer.organization_id == org_id,
                    Answer.evaluation_id == evaluation.id,
                )
            )
            or 0
        )
    risk_by_id = {risk.id: risk for risk in risks}
    levels = Counter(str(risk.inherent_level) for risk in risks)
    urgent = sum(
        risk.inherent_level in ("critical", "high") and risk.status != "closed" for risk in risks
    )
    now = datetime.now(UTC)
    overdue = sum(
        item.target_date is not None and item.target_date < now.date() and item.progress < 100
        for item in treatments
    )
    maturity = (
        f"{scores['current_profile']:.1f}%" if scores and scores["answered"] else "Sin evaluar"
    )
    return {
        "id": str(report.id),
        "title": report.title,
        "scope": report.scope,
        "organization": organization.name if organization else "No registrado",
        "profile": {
            "sector": organization.sector,
            "size": organization.size,
            "country": organization.country,
            "slug": organization.slug,
        }
        if organization
        else {},
        "prepared_by": creator.full_name if creator else "No registrado",
        "generated_at": now.strftime("%d/%m/%Y · %H:%M UTC"),
        "summary": f"Inventario: {len(assets)} activos. Riesgos registrados: {len(risks)}. "
        f"Riesgos altos o críticos sin cerrar: {urgent}. Acciones de tratamiento vencidas: "
        f"{overdue}. Madurez de la evaluación más reciente: {maturity}.",
        "metrics": [
            {"label": "Activos registrados", "value": len(assets)},
            {"label": "Riesgos registrados", "value": len(risks)},
            {"label": "Madurez NIST CSF", "value": maturity},
            {
                "label": "Incidentes sin resolver",
                "value": sum(item.status != "resolved" for item in incidents),
            },
        ],
        "risk_levels": dict(levels),
        "evidence_count": evidence_count,
        "evaluation": {
            "code": evaluation.code,
            "name": evaluation.name,
            "status": str(evaluation.status),
            "version": evaluation.version,
            "scope": evaluation.scope,
        }
        if evaluation
        else None,
        "scores": scores,
        "risks": [
            {
                "code": r.code,
                "title": r.title,
                "level": str(r.inherent_level),
                "score": r.inherent_score,
                "residual": r.residual_score,
                "strategy": str(r.treatment_strategy),
                "status": str(r.status),
                "progress": r.progress,
                "description": r.description,
                "controls": r.existing_controls,
                "owner": users.get(r.responsible_user_id) if r.responsible_user_id else None,
                "date": str(r.target_date) if r.target_date else None,
            }
            for r in risks
        ],
        "actions": [
            {
                "risk": risk_by_id[t.risk_id].code,
                "action": t.action,
                "owner": users.get(t.responsible_user_id) if t.responsible_user_id else None,
                "date": str(t.target_date) if t.target_date else None,
                "progress": t.progress,
                "overdue": bool(t.target_date and t.target_date < now.date() and t.progress < 100),
            }
            for t in treatments
        ],
        "assets": [
            {
                "code": a.internal_code,
                "name": a.name,
                "type": str(a.asset_type),
                "criticality": a.overall_criticality,
                "owner": a.owner,
                "exposure": str(a.exposure_level),
                "status": str(a.status),
            }
            for a in assets
        ],
        "incidents": [
            {
                "title": i.title,
                "severity": str(i.severity),
                "status": str(i.status),
                "date": i.occurred_at.strftime("%d/%m/%Y"),
            }
            for i in incidents
        ],
    }
