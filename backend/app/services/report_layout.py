# ruff: noqa: E501
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

NAVY = colors.HexColor("#0b2540")
CYAN = colors.HexColor("#087f9c")
PALE = colors.HexColor("#f0f5fa")
GRAY = colors.HexColor("#52657a")
LINE = colors.HexColor("#dce5ee")
LEVELS = [
    ("critical", "Crítico", "#bd3439"),
    ("high", "Alto", "#c45d20"),
    ("medium", "Medio", "#a77812"),
    ("low", "Bajo", "#188269"),
]
LABELS = {
    "critical": "Crítico",
    "high": "Alto",
    "medium": "Medio",
    "low": "Bajo",
    "identified": "Identificado",
    "analyzing": "En análisis",
    "in_treatment": "En tratamiento",
    "accepted": "Aceptado",
    "closed": "Cerrado",
    "mitigate": "Mitigar",
    "avoid": "Evitar",
    "transfer": "Transferir",
    "accept": "Aceptar",
    "server": "Servidor",
    "computer": "Computadora",
    "mobile": "Móvil",
    "network": "Red",
    "application": "Aplicación",
    "database": "Base de datos",
    "information": "Información",
    "cloud_service": "Servicio en nube",
    "critical_account": "Cuenta crítica",
    "supplier": "Proveedor",
    "other": "Otro",
    "internal": "Interna",
    "limited": "Limitada",
    "public": "Pública",
    "active": "Activo",
    "inactive": "Inactivo",
    "maintenance": "Mantenimiento",
    "retired": "Retirado",
    "open": "Abierto",
    "investigating": "En investigación",
    "contained": "Contenido",
    "resolved": "Resuelto",
    "draft": "Borrador",
    "in_review": "En revisión",
    "approved": "Aprobado",
}


def build_pdf(path: Path, report_type: str, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    width = 174 * mm - 12
    styles = {
        "body": ParagraphStyle(
            "body", fontName="Helvetica", fontSize=9, leading=13, textColor=NAVY, spaceAfter=6
        ),
        "small": ParagraphStyle(
            "small", fontName="Helvetica", fontSize=7.5, leading=10, textColor=GRAY,
            spaceAfter=5, keepWithNext=True
        ),
        "cell": ParagraphStyle(
            "cell",
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=NAVY,
            splitLongWords=True,
        ),
        "head": ParagraphStyle(
            "head", fontName="Helvetica-Bold", fontSize=7.5, leading=10, textColor=colors.white
        ),
        "section": ParagraphStyle(
            "section",
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=17,
            textColor=NAVY,
            spaceBefore=14,
            spaceAfter=8,
            keepWithNext=True,
        ),
        "title": ParagraphStyle(
            "title",
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=28,
            textColor=NAVY,
            spaceAfter=12,
        ),
        "kicker": ParagraphStyle(
            "kicker",
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=11,
            textColor=CYAN,
            spaceAfter=7,
        ),
        "metric": ParagraphStyle(
            "metric", fontName="Helvetica-Bold", fontSize=20, leading=24, textColor=NAVY
        ),
    }

    def p(value: Any, style: str = "body") -> Paragraph:
        text = "No registrado" if value is None or value == "" else str(value)
        return Paragraph(escape(text).replace("\n", "<br/>"), styles[style])

    def label(value: Any) -> str:
        return LABELS.get(str(value), str(value)) if value else "No registrado"

    def table(headers: list[str], rows: list[list[Any]], sizes: list[float]) -> Table:
        cells = [[p(v, "head") for v in headers]] + [[p(v, "cell") for v in row] for row in rows]
        result = Table(
            cells,
            colWidths=[width * size for size in sizes],
            repeatRows=1,
            hAlign="LEFT",
            splitInRow=1,
        )
        result.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE]),
                    ("LINEBELOW", (0, 0), (-1, 0), 1, CYAN),
                    ("LINEBELOW", (0, 1), (-1, -1), 0.35, LINE),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 7),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        return result

    executive = report_type == "executive"
    generated = data.get("generated_at", datetime.now(UTC).strftime("%d/%m/%Y · %H:%M UTC"))
    story: list[Any] = [
        p("INFORME EJECUTIVO" if executive else "INFORME TÉCNICO", "kicker"),
        p(data["title"], "title"),
        p(data["organization"]),
        p(
            f"Generado: {generated} | Preparado por: {data.get('prepared_by', 'No registrado')}",
            "small",
        ),
        p(f"Alcance declarado: {data['scope']}", "small"),
        p("01  Resumen ejecutivo", "section"),
        p(data["summary"]),
    ]
    metrics = data.get("metrics", [])
    if metrics:
        cards = Table(
            [
                [
                    [p(item["value"], "metric"), Spacer(1, 5), p(item["label"], "small")]
                    for item in metrics
                ]
            ],
            colWidths=[width / len(metrics)] * len(metrics),
        )
        cards.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), PALE),
                    ("BOX", (0, 0), (-1, -1), 0.5, LINE),
                    ("INNERGRID", (0, 0), (-1, -1), 3, colors.white),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ]
            )
        )
        story.extend([Spacer(1, 6), cards])
    profile = data.get("profile", {})
    if profile:
        story.extend(
            [
                p("Perfil de la empresa", "section"),
                table(
                    ["Sector", "Tamaño", "País", "Identificador"],
                    [
                        [
                            profile.get("sector"),
                            profile.get("size"),
                            profile.get("country"),
                            profile.get("slug"),
                        ]
                    ],
                    [0.25, 0.25, 0.15, 0.35],
                ),
            ]
        )
    risks = data.get("risks", [])
    story.append(p("02  Panorama de riesgo", "section"))
    distribution = data.get("risk_levels", {})
    if distribution:
        chart = Drawing(width, 76)
        max_count = max(distribution.values()) or 1
        for i, (code, title, color) in enumerate(LEVELS):
            y = 59 - i * 18
            count = distribution.get(code, 0)
            chart.add(String(0, y, title, fontName="Helvetica", fontSize=8, fillColor=NAVY))
            track = Rect(60, y - 1, width - 95, 9)
            track.fillColor = PALE
            track.strokeColor = None
            chart.add(track)
            if count:
                bar = Rect(60, y - 1, (width - 95) * count / max_count, 9)
                bar.fillColor = colors.HexColor(color)
                bar.strokeColor = None
                chart.add(bar)
            chart.add(
                String(
                    width - 20, y, str(count), fontName="Helvetica-Bold", fontSize=8, fillColor=NAVY
                )
            )
        story.extend(
            [
                chart,
                p(
                    "Distribución por nivel inherente de todos los riesgos registrados, incluidos los cerrados.",
                    "small",
                ),
            ]
        )
    story.append(p("Principales riesgos", "section"))
    visible_risks = risks[:8] if executive else risks
    if risks:
        story.extend(
            [
                p(
                    f"{len(visible_risks)} de {len(risks)} riesgos, ordenados por puntaje inherente descendente. Puntajes sobre 25.",
                    "small",
                ),
                table(
                    ["Código / riesgo", "Nivel", "Inherente / residual", "Estado", "Avance"],
                    [
                        [
                            f"{r['code']} · {r['title']}",
                            label(r["level"]),
                            f"{r['score']} / {r.get('residual', 'N/D')}",
                            label(r.get("status")),
                            f"{r.get('progress', 0)}%",
                        ]
                        for r in visible_risks
                    ],
                    [0.4, 0.12, 0.16, 0.2, 0.12],
                ),
            ]
        )
    else:
        story.append(p("No hay riesgos registrados. Esto no implica ausencia de riesgo."))
    story.extend([PageBreak(), p("03  Madurez y controles", "section")])
    evaluation = data.get("evaluation")
    scores = data.get("scores")
    if evaluation and scores:
        story.append(
            p(
                f"{evaluation['code']} · {evaluation['name']} · Versión {evaluation['version']} · {label(evaluation['status'])}"
            )
        )
        story.append(p(f"Alcance de la evaluación: {evaluation['scope']}", "small"))
        story.append(
            p(
                f"Última evaluación creada. Respuestas: {scores['answered']} de {scores['total']}. Evidencias registradas: {data.get('evidence_count', 0)}.",
                "small",
            )
        )
        story.append(
            table(
                ["Función NIST CSF 2.0", "Madurez", "Objetivo", "Respuestas"],
                [
                    [
                        f"{f['code']} · {f['name']}",
                        f"{f['score']:.1f}%" if f["answered"] else "Sin evaluar",
                        f"{f['target']:.1f}%",
                        f"{f['answered']} / {f['total']}",
                    ]
                    for f in scores["by_function"]
                ],
                [0.49, 0.17, 0.17, 0.17],
            )
        )
        story.append(
            p(
                "Cálculo idéntico al módulo de evaluaciones: respuestas ponderadas sobre una escala de 0 a 4; preguntas pendientes aportan cero. No se mezclan evaluaciones ni versiones. Sin respuestas se indica «Sin evaluar».",
                "small",
            )
        )
    else:
        story.append(
            p(
                "Sin evaluación registrada. La madurez no puede determinarse con los datos disponibles."
            )
        )
    actions = data.get("actions", [])
    selected_actions = actions[:10] if executive else actions
    story.append(p("04  Plan de acción registrado", "section"))
    if actions:
        story.append(
            p(
                f"{len(selected_actions)} de {len(actions)} acciones, priorizadas por riesgo inherente y fecha objetivo. Se conservan las acciones completadas para seguimiento.",
                "small",
            )
        )
        story.append(
            table(
                ["Riesgo / acción", "Responsable", "Fecha objetivo", "Avance"],
                [
                    [
                        f"{a['risk']} · {a['action']}",
                        a["owner"],
                        f"{a['date']} (vencida)" if a["overdue"] else a["date"],
                        f"{a['progress']}%",
                    ]
                    for a in selected_actions
                ],
                [0.46, 0.22, 0.2, 0.12],
            )
        )
    else:
        story.append(
            p(
                "No hay acciones de tratamiento registradas. Defina las acciones, responsables y fechas en Gestión de riesgos."
            )
        )
    assets = data.get("assets", [])
    shown_assets = [a for a in assets if a["criticality"] >= 4][:6] if executive else assets
    if not executive:
        story.append(PageBreak())
    story.append(p("05  Activos críticos" if executive else "05  Inventario incluido", "section"))
    if shown_assets:
        story.append(
            p(
                f"{len(shown_assets)} de {len(assets)} activos registrados. "
                + (
                    "Selección con criticidad de 4 o 5, hasta seis activos."
                    if executive
                    else "Inventario completo ordenado por criticidad."
                ),
                "small",
            )
        )
        story.append(
            table(
                ["Código / activo", "Tipo", "Responsable", "Exposición", "Crit."],
                [
                    [
                        f"{a['code']} · {a['name']}",
                        label(a["type"]),
                        a.get("owner"),
                        label(a.get("exposure")),
                        f"{a['criticality']}/5",
                    ]
                    for a in shown_assets
                ],
                [0.36, 0.18, 0.22, 0.14, 0.1],
            )
        )
    else:
        story.append(
            p(
                "No hay activos con criticidad de 4 o 5 registrados."
                if executive
                else "No hay activos registrados."
            )
        )
    incidents = data.get("incidents", [])
    if incidents:
        story.append(p("06  Incidentes registrados", "section"))
        selected = incidents[:5] if executive else incidents
        story.append(
            p(
                f"{len(selected)} de {len(incidents)} incidentes, del más reciente al más antiguo.",
                "small",
            )
        )
        story.append(
            table(
                ["Incidente", "Severidad", "Estado", "Fecha"],
                [
                    [i["title"], label(i["severity"]), label(i["status"]), i["date"]]
                    for i in selected
                ],
                [0.46, 0.16, 0.22, 0.16],
            )
        )
    if not executive and risks:
        story.append(p("Detalle de riesgos y tratamientos", "section"))
        for risk in risks:
            story.append(p(f"{risk['code']} · {risk['title']}", "section"))
            story.append(p(risk.get("description")))
            story.append(
                p(
                    f"Estrategia: {label(risk['strategy'])}. Responsable: {risk.get('owner') or 'No registrado'}. Fecha objetivo: {risk.get('date') or 'No registrado'}.",
                    "small",
                )
            )
            story.append(p(f"Controles existentes: {risk.get('controls') or 'No registrado'}"))
    story.append(
        KeepTogether(
            [
                p("Trazabilidad y lectura del informe", "section"),
                p(
                    "Fuente: registros de la empresa seleccionada al generar el documento, excluyendo eliminados. El alcance declarado es descriptivo y no filtra los datos. Los campos faltantes se indican como «No registrado».",
                    "small",
                ),
                p(
                    "Los puntajes de riesgo son los almacenados por el sistema (probabilidad × impacto, matriz 5 × 5). El documento refleja una autoevaluación y no constituye una certificación.",
                    "small",
                ),
            ]
        )
    )

    if executive:
        traceability = story.pop()
        first_break = next(i for i, item in enumerate(story) if isinstance(item, PageBreak))
        story.insert(first_break, traceability)

    def frame(canvas, document):  # type: ignore[no-untyped-def]
        canvas.saveState()
        canvas.setFillColor(NAVY)
        canvas.rect(0, A4[1] - 16 * mm, A4[0], 16 * mm, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 8)
        canvas.drawString(18 * mm, A4[1] - 10 * mm, "SECURECOMMERCE ADVISOR")
        canvas.setFont("Helvetica", 7)
        canvas.drawRightString(192 * mm, A4[1] - 10 * mm, "CONFIDENCIAL · USO INTERNO")
        canvas.setStrokeColor(LINE)
        canvas.line(18 * mm, 15 * mm, 192 * mm, 15 * mm)
        canvas.setFillColor(GRAY)
        canvas.setFont("Helvetica", 6.5)
        canvas.drawString(18 * mm, 10 * mm, f"ID: {data.get('id', 'No registrado')}")
        canvas.drawRightString(192 * mm, 10 * mm, f"Página {document.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=24 * mm,
        bottomMargin=22 * mm,
        title=str(data["title"]),
        author="SecureCommerce Advisor",
    )
    doc.build(story, onFirstPage=frame, onLaterPages=frame)
