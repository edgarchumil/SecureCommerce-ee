import asyncio
import os
from datetime import UTC, datetime

from sqlalchemy import select

from app.core.database import SessionFactory, dispose_engine
from app.models.assets import Asset, AssetStatus, AssetType, ExposureLevel
from app.models.evaluations import (
    Answer,
    Evaluation,
    EvaluationAsset,
    FrameworkCategory,
    FrameworkControl,
    FrameworkFunction,
    Question,
)
from app.models.identity import Membership, Organization, RoleCode, User
from app.models.operations import Incident, IncidentSeverity, Notification
from app.models.risks import (
    Risk,
    RiskLevel,
    RiskStatus,
    RiskTreatment,
    Threat,
    TreatmentStrategy,
    Vulnerability,
)
from app.security.passwords import hash_password
from app.standards.nist_csf import seed_nist_csf

DEMO_USERS = (
    ("administrador@demo.local", "Administración Demo", RoleCode.ORG_ADMIN),
    ("analista@demo.local", "Analista Demo", RoleCode.ANALYST),
    ("consulta@demo.local", "Consulta Demo", RoleCode.VIEWER),
)


async def seed() -> None:
    password = os.getenv("DEMO_PASSWORD")
    if not password or len(password) < 12:
        raise RuntimeError("Defina DEMO_PASSWORD con al menos 12 caracteres")
    async with SessionFactory() as db:
        framework = await seed_nist_csf(db)
        organization = await db.scalar(
            select(Organization).where(Organization.slug == "comercializadora-maya")
        )
        if organization is None:
            organization = Organization(
                name="Comercializadora Maya, S.A.",
                slug="comercializadora-maya",
                sector="Comercio",
                size="Pequeña empresa",
                country="GT",
            )
            db.add(organization)
            await db.flush()
        for email, full_name, role in DEMO_USERS:
            user = await db.scalar(select(User).where(User.email == email))
            if user is None:
                user = User(
                    email=email,
                    full_name=full_name,
                    password_hash=hash_password(password),
                    is_active=True,
                )
                db.add(user)
                await db.flush()
            if email == "administrador@demo.local":
                user.is_superadmin = True
            membership = await db.scalar(
                select(Membership).where(
                    Membership.organization_id == organization.id,
                    Membership.user_id == user.id,
                )
            )
            if membership is None:
                db.add(
                    Membership(
                        organization_id=organization.id,
                        user_id=user.id,
                        role_code=role,
                    )
                )
        second_organization = await db.scalar(
            select(Organization).where(Organization.slug == "servicios-del-lago")
        )
        if second_organization is None:
            second_organization = Organization(
                name="Servicios del Lago, S.A.",
                slug="servicios-del-lago",
                sector="Servicios profesionales",
                size="Microempresa",
                country="GT",
            )
            db.add(second_organization)
            await db.flush()
        creator = await db.scalar(select(User).where(User.email == "administrador@demo.local"))
        assert creator is not None
        second_membership = await db.scalar(
            select(Membership).where(
                Membership.organization_id == second_organization.id,
                Membership.user_id == creator.id,
            )
        )
        if second_membership is None:
            db.add(
                Membership(
                    organization_id=second_organization.id,
                    user_id=creator.id,
                    role_code=RoleCode.ORG_ADMIN,
                )
            )
        demo_assets = (
            ("Servidor de facturación", "SRV-FACT-01", AssetType.SERVER, 5),
            ("Computadora de gerencia", "PC-GER-01", AssetType.COMPUTER, 4),
            ("Router principal", "NET-RTR-01", AssetType.NETWORK, 5),
            ("Base de datos de clientes", "DB-CLI-01", AssetType.DATABASE, 5),
            ("Correo corporativo", "APP-MAIL-01", AssetType.CLOUD_SERVICE, 4),
            ("Sitio web de comercio electrónico", "APP-WEB-01", AssetType.APPLICATION, 5),
            ("Servicio de almacenamiento en la nube", "CLD-STO-01", AssetType.CLOUD_SERVICE, 4),
        )
        for name, code, asset_type, criticality in demo_assets:
            exists = await db.scalar(
                select(Asset.id).where(
                    Asset.organization_id == organization.id,
                    Asset.internal_code == code,
                )
            )
            if exists is None:
                db.add(
                    Asset(
                        organization_id=organization.id,
                        created_by=creator.id,
                        name=name,
                        internal_code=code,
                        asset_type=asset_type,
                        description="Dato ficticio para demostración",
                        exposure_level=ExposureLevel.INTERNAL,
                        status=AssetStatus.ACTIVE,
                        confidentiality_criticality=criticality,
                        integrity_criticality=criticality,
                        availability_criticality=criticality,
                        overall_criticality=criticality,
                        tags=["demo", "ficticio"],
                        outgoing_dependencies=[],
                    )
                )
        await db.flush()
        threat = await db.scalar(
            select(Threat).where(
                Threat.organization_id == organization.id,
                Threat.name == "Campaña de phishing",
            )
        )
        if threat is None:
            threat = Threat(
                organization_id=organization.id,
                created_by=creator.id,
                name="Campaña de phishing",
                description="Amenaza ficticia de suplantación dirigida al personal.",
                likelihood=4,
            )
            db.add(threat)
        vulnerability = await db.scalar(
            select(Vulnerability).where(
                Vulnerability.organization_id == organization.id,
                Vulnerability.name == "MFA pendiente",
            )
        )
        if vulnerability is None:
            vulnerability = Vulnerability(
                organization_id=organization.id,
                created_by=creator.id,
                name="MFA pendiente",
                description="Cuentas ficticias sin segundo factor habilitado.",
                severity=4,
            )
            db.add(vulnerability)
        await db.flush()
        demo_risk = await db.scalar(
            select(Risk).where(
                Risk.organization_id == organization.id,
                Risk.code == "RSK-DEMO-001",
            )
        )
        if demo_risk is None:
            mail_asset = await db.scalar(
                select(Asset).where(
                    Asset.organization_id == organization.id,
                    Asset.internal_code == "APP-MAIL-01",
                )
            )
            assert mail_asset is not None
            demo_risk = Risk(
                organization_id=organization.id,
                created_by=creator.id,
                code="RSK-DEMO-001",
                title="Compromiso de correo por phishing",
                description="Escenario ficticio para demostrar priorización y tratamiento.",
                asset_id=mail_asset.id,
                threat_id=threat.id,
                vulnerability_id=vulnerability.id,
                probability=4,
                impact=5,
                inherent_score=20,
                inherent_level=RiskLevel.CRITICAL,
                existing_controls="Filtro antispam y capacitación inicial.",
                residual_probability=2,
                residual_impact=4,
                residual_score=8,
                residual_level=RiskLevel.MEDIUM,
                treatment_strategy=TreatmentStrategy.MITIGATE,
                responsible_user_id=creator.id,
                progress=35,
                status=RiskStatus.IN_TREATMENT,
            )
            db.add(demo_risk)
            await db.flush()
            db.add(
                RiskTreatment(
                    organization_id=organization.id,
                    risk_id=demo_risk.id,
                    created_by=creator.id,
                    action="Habilitar MFA y ejecutar una simulación de phishing.",
                    responsible_user_id=creator.id,
                    progress=35,
                    notes="Acción ficticia de demostración.",
                )
            )
        demo_evaluation = await db.scalar(
            select(Evaluation).where(
                Evaluation.organization_id == organization.id,
                Evaluation.code == "NIST-DEMO-2026",
                Evaluation.version == 1,
            )
        )
        if demo_evaluation is None:
            asset_ids = list(
                (
                    await db.scalars(
                        select(Asset.id).where(Asset.organization_id == organization.id)
                    )
                ).all()
            )
            demo_evaluation = Evaluation(
                organization_id=organization.id,
                created_by=creator.id,
                framework_id=framework.id,
                code="NIST-DEMO-2026",
                name="Evaluación NIST de demostración",
                scope="Toda la organización; datos exclusivamente ficticios.",
                target_maturity=3,
                comments="Evaluación ficticia para explorar el MVP.",
                assets=[],
                answers=[],
            )
            db.add(demo_evaluation)
            await db.flush()
            demo_evaluation.assets.extend(
                EvaluationAsset(
                    organization_id=organization.id,
                    evaluation_id=demo_evaluation.id,
                    asset_id=asset_id,
                )
                for asset_id in asset_ids
            )
            question_ids = list(
                (
                    await db.scalars(
                        select(Question.id)
                        .join(FrameworkControl)
                        .join(FrameworkCategory)
                        .join(FrameworkFunction)
                        .where(FrameworkFunction.framework_id == framework.id)
                    )
                ).all()
            )
            demo_evaluation.answers.extend(
                Answer(
                    organization_id=organization.id,
                    evaluation_id=demo_evaluation.id,
                    question_id=question_id,
                    answered_by=creator.id,
                    maturity=2,
                    comment="Respuesta ficticia de demostración.",
                )
                for question_id in question_ids
            )
        incident = await db.scalar(
            select(Incident).where(
                Incident.organization_id == organization.id,
                Incident.title == "Intento de acceso sospechoso (demostración)",
            )
        )
        if incident is None:
            db.add(
                Incident(
                    organization_id=organization.id,
                    created_by=creator.id,
                    title="Intento de acceso sospechoso (demostración)",
                    description=(
                        "Evento completamente ficticio para explorar el seguimiento de incidentes."
                    ),
                    severity=IncidentSeverity.MEDIUM,
                    occurred_at=datetime.now(UTC),
                )
            )
        notification = await db.scalar(
            select(Notification).where(
                Notification.organization_id == organization.id,
                Notification.user_id == creator.id,
                Notification.title == "Bienvenido al MVP",
            )
        )
        if notification is None:
            db.add(
                Notification(
                    organization_id=organization.id,
                    user_id=creator.id,
                    title="Bienvenido al MVP",
                    message="Revise los indicadores y acciones ficticias de demostración.",
                    link="/panel",
                )
            )
        await db.commit()
    await dispose_engine()
    print("Seed demostrativo completo creado o actualizado.")


if __name__ == "__main__":
    asyncio.run(seed())
