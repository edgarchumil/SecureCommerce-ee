from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evaluations import (
    Framework,
    FrameworkCategory,
    FrameworkControl,
    FrameworkFunction,
    Question,
)

OPTIONS = [
    {"value": 0, "label": "No implementado"},
    {"value": 1, "label": "Inicial"},
    {"value": 2, "label": "Parcial"},
    {"value": 3, "label": "Implementado"},
    {"value": 4, "label": "Gestionado"},
]

CATALOG = (
    (
        "GV",
        "Govern",
        "GV.OC",
        "Contexto organizacional",
        "GV.OC-01",
        "Contexto de seguridad",
        "¿La empresa documenta sus objetivos de ciberseguridad y responsables?",
        "Defina responsables y relacione la seguridad con las necesidades del negocio.",
        "Política, organigrama o acta de asignación.",
        "Documente objetivos y responsables de ciberseguridad.",
    ),
    (
        "ID",
        "Identify",
        "ID.AM",
        "Gestión de activos",
        "ID.AM-01",
        "Inventario",
        "¿Existe un inventario actualizado de equipos, aplicaciones, datos y servicios?",
        "Incluya recursos propios, en la nube y de proveedores.",
        "Inventario fechado con propietario y criticidad.",
        "Complete y revise trimestralmente el inventario.",
    ),
    (
        "PR",
        "Protect",
        "PR.AA",
        "Gestión de identidades",
        "PR.AA-01",
        "Control de acceso",
        "¿Cada persona utiliza una cuenta individual con acceso según su función?",
        "Evite cuentas compartidas y retire accesos al finalizar una relación laboral.",
        "Listado de cuentas, roles y revisiones de acceso.",
        "Asigne cuentas individuales y revise permisos.",
    ),
    (
        "DE",
        "Detect",
        "DE.CM",
        "Monitoreo continuo",
        "DE.CM-01",
        "Monitoreo",
        "¿Se revisan alertas y registros para detectar actividad inusual?",
        "Determine quién revisa alertas y con qué frecuencia.",
        "Registros de revisión o alertas atendidas.",
        "Establezca una revisión periódica de alertas.",
    ),
    (
        "RS",
        "Respond",
        "RS.MA",
        "Gestión de respuesta",
        "RS.MA-01",
        "Plan de respuesta",
        "¿Existe un plan sencillo para responder a incidentes de seguridad?",
        "Incluya contactos, prioridades y pasos para contener y comunicar.",
        "Plan aprobado y evidencia de simulacro.",
        "Cree y pruebe un plan básico de respuesta.",
    ),
    (
        "RC",
        "Recover",
        "RC.RP",
        "Ejecución de recuperación",
        "RC.RP-01",
        "Recuperación",
        "¿Las copias de seguridad se prueban mediante restauraciones?",
        "Una copia no está confirmada hasta que se restaura correctamente.",
        "Registro de restauración con fecha y resultado.",
        "Programe pruebas documentadas de restauración.",
    ),
)


async def seed_nist_csf(db: AsyncSession) -> Framework:
    existing = await db.scalar(
        select(Framework).where(Framework.code == "NIST-CSF", Framework.version == "2.0")
    )
    if existing:
        return existing
    framework = Framework(
        code="NIST-CSF",
        name="NIST Cybersecurity Framework",
        version="2.0",
        description="Catálogo inicial adaptado a MIPYMES guatemaltecas.",
    )
    db.add(framework)
    await db.flush()
    for order, item in enumerate(CATALOG, start=1):
        (
            function_code,
            function_name,
            category_code,
            category_name,
            control_code,
            control_title,
            text,
            help_text,
            evidence,
            recommendation,
        ) = item
        function = FrameworkFunction(
            framework_id=framework.id, code=function_code, name=function_name, sort_order=order
        )
        db.add(function)
        await db.flush()
        category = FrameworkCategory(
            function_id=function.id, code=category_code, name=category_name, sort_order=1
        )
        db.add(category)
        await db.flush()
        control = FrameworkControl(category_id=category.id, code=control_code, title=control_title)
        db.add(control)
        await db.flush()
        db.add(
            Question(
                control_id=control.id,
                text=text,
                help_text=help_text,
                weight=1.0,
                expected_evidence=evidence,
                response_options=OPTIONS,
                base_recommendation=recommendation,
                sort_order=1,
            )
        )
    await db.flush()
    return framework
