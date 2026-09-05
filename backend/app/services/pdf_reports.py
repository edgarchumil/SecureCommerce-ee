# ruff: noqa: E501
from __future__ import annotations

from datetime import UTC, datetime
from html import escape
from pathlib import Path
from typing import Any

from reportlab.graphics.charts.barcharts import HorizontalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.shapes import Drawing, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

NAVY = colors.HexColor("#08243F")
BLUE = colors.HexColor("#155EEF")
CYAN = colors.HexColor("#06B6D4")
INK = colors.HexColor("#172B4D")
MUTED = colors.HexColor("#5E6C84")
LIGHT = colors.HexColor("#F4F7FB")
BORDER = colors.HexColor("#DCE3EC")
GREEN = colors.HexColor("#16865C")
AMBER = colors.HexColor("#D97706")
RED = colors.HexColor("#C93737")
WHITE = colors.white

LEVELS = {"critical": "Crítico", "high": "Alto", "medium": "Medio", "low": "Bajo"}
STATUSES = {
    "identified": "Identificado",
    "analyzing": "En análisis",
    "in_treatment": "En tratamiento",
    "accepted": "Aceptado",
    "closed": "Cerrado",
}
STRATEGIES = {
    "avoid": "Evitar",
    "mitigate": "Mitigar",
    "transfer": "Transferir",
    "accept": "Aceptar",
}
ASSET_TYPES = {
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
}
EXPOSURES = {"internal": "Interna", "limited": "Limitada", "public": "Pública"}
COUNTRIES = {"GT": "Guatemala"}


def _value(value: object | None, fallback: str = "No registrado") -> str:
    text = str(value or "").strip()
    return text or fallback


def _enum(value: object | None) -> str:
    return str(value or "").split(".")[-1].lower()


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "body": ParagraphStyle(
            "BodySC",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.2,
            leading=13,
            textColor=INK,
            spaceAfter=5,
        ),
        "small": ParagraphStyle(
            "SmallSC",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=7.4,
            leading=10,
            textColor=MUTED,
        ),
        "eyebrow": ParagraphStyle(
            "EyebrowSC",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=CYAN,
            spaceAfter=7,
        ),
        "cover_title": ParagraphStyle(
            "CoverTitleSC",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=27,
            leading=32,
            textColor=WHITE,
            alignment=TA_LEFT,
            spaceAfter=12,
        ),
        "cover_org": ParagraphStyle(
            "CoverOrgSC",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=20,
            textColor=WHITE,
            spaceAfter=4,
        ),
        "cover_meta": ParagraphStyle(
            "CoverMetaSC",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=14,
            textColor=colors.HexColor("#D7E5F2"),
        ),
        "h1": ParagraphStyle(
            "H1SC",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=23,
            textColor=NAVY,
            spaceAfter=10,
        ),
        "h2": ParagraphStyle(
            "H2SC",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=16,
            textColor=BLUE,
            spaceBefore=11,
            spaceAfter=6,
        ),
        "card_value": ParagraphStyle(
            "CardValueSC",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=21,
            textColor=NAVY,
            alignment=TA_CENTER,
        ),
        "card_label": ParagraphStyle(
            "CardLabelSC",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=9,
            textColor=MUTED,
            alignment=TA_CENTER,
        ),
        "table": ParagraphStyle(
            "TableSC",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=7.2,
            leading=9,
            textColor=INK,
        ),
        "table_head": ParagraphStyle(
            "TableHeadSC",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=7.2,
            leading=9,
            textColor=WHITE,
        ),
    }


def _p(value: object, style: ParagraphStyle) -> Paragraph:
    return Paragraph(escape(_value(value)), style)


def _cover(canvas: Any, _doc: BaseDocTemplate, _data: dict[str, Any]) -> None:
    canvas.saveState()
    width, height = A4
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, width, height, fill=1, stroke=0)
    canvas.setFillColor(CYAN)
    canvas.rect(0, 0, 9 * mm, height, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor("#0C3355"))
    canvas.circle(width - 14 * mm, height - 20 * mm, 52 * mm, fill=1, stroke=0)
    canvas.circle(width - 4 * mm, 16 * mm, 35 * mm, fill=1, stroke=0)
    canvas.restoreState()


def _header_footer(canvas: Any, doc: BaseDocTemplate, data: dict[str, Any]) -> None:
    canvas.saveState()
    width, height = A4
    canvas.setFillColor(NAVY)
    canvas.rect(0, height - 13 * mm, width, 13 * mm, fill=1, stroke=0)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.setFillColor(WHITE)
    canvas.drawString(18 * mm, height - 8.5 * mm, "SECURECOMMERCE ADVISOR")
    canvas.drawRightString(
        width - 18 * mm, height - 8.5 * mm, _value(data.get("organization"), "Organización")
    )
    canvas.setStrokeColor(BORDER)
    canvas.line(18 * mm, 14 * mm, width - 18 * mm, 14 * mm)
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(18 * mm, 9 * mm, "Confidencial · Uso interno")
    canvas.drawCentredString(width / 2, 9 * mm, f"ID: {_value(data.get('report_id'), 'N/D')}")
    canvas.drawRightString(width - 18 * mm, 9 * mm, f"Página {doc.page}")
    canvas.restoreState()


def _table(
    rows: list[list[object]], widths: list[float], styles: dict[str, ParagraphStyle]
) -> Table:
    content = [
        [_p(cell, styles["table_head"] if index == 0 else styles["table"]) for cell in row]
        for index, row in enumerate(rows)
    ]
    table = Table(content, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT]),
                ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def _metric_cards(metrics: list[dict[str, object]], styles: dict[str, ParagraphStyle]) -> Table:
    cells = [
        [
            Paragraph(f"<b>{escape(_value(item.get('value')))}</b>", styles["card_value"]),
            _p(item.get("label"), styles["card_label"]),
        ]
        for item in metrics[:4]
    ]
    table = Table([cells], colWidths=[39 * mm] * len(cells), rowHeights=[26 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
                ("BOX", (0, 0), (-1, -1), 0.6, BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 3, WHITE),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    return table


def _risk_chart(distribution: dict[str, int]) -> Drawing:
    drawing = Drawing(155 * mm, 40 * mm)
    values = [distribution.get(key, 0) for key in ("critical", "high", "medium", "low")]
    if not sum(values):
        drawing.add(
            String(
                3 * mm,
                18 * mm,
                "No hay riesgos registrados en el alcance.",
                fontName="Helvetica",
                fontSize=9,
                fillColor=MUTED,
            )
        )
        return drawing
    pie = Pie()
    pie.x, pie.y, pie.width, pie.height = 5 * mm, 3 * mm, 34 * mm, 34 * mm
    pie.data, pie.labels = values, [str(value) for value in values]
    for index, color in enumerate((RED, colors.HexColor("#E0642B"), AMBER, GREEN)):
        pie.slices[index].fillColor, pie.slices[index].strokeWidth = color, 0.5
    drawing.add(pie)
    for index, (label, color, value) in enumerate(
        zip(
            ("Críticos", "Altos", "Medios", "Bajos"),
            (RED, colors.HexColor("#E0642B"), AMBER, GREEN),
            values,
            strict=True,
        )
    ):
        y = 31 * mm - index * 8 * mm
        drawing.add(String(53 * mm, y, "●", fontName="Helvetica", fontSize=10, fillColor=color))
        drawing.add(
            String(
                60 * mm, y, f"{label}: {value}", fontName="Helvetica", fontSize=8.5, fillColor=INK
            )
        )
    return drawing


def _maturity_chart(functions: list[dict[str, object]]) -> Drawing:
    drawing = Drawing(155 * mm, 50 * mm)
    if not functions:
        drawing.add(
            String(
                3 * mm,
                22 * mm,
                "Sin respuestas suficientes para desglosar la madurez.",
                fontName="Helvetica",
                fontSize=8.5,
                fillColor=MUTED,
            )
        )
        return drawing
    chart = HorizontalBarChart()
    chart.x, chart.y, chart.width, chart.height = 39 * mm, 5 * mm, 108 * mm, 39 * mm
    chart.data = [[float(item.get("percent", 0)) for item in functions[:6]]]
    chart.categoryAxis.categoryNames = [_value(item.get("code")) for item in functions[:6]]
    chart.valueAxis.valueMin, chart.valueAxis.valueMax, chart.valueAxis.valueStep = 0, 100, 25
    chart.valueAxis.labelTextFormat = "%d%%"
    chart.bars[0].fillColor = chart.bars[0].strokeColor = BLUE
    chart.barWidth = 4 * mm
    chart.categoryAxis.labels.fontSize = 7
    chart.valueAxis.labels.fontSize = 6.5
    drawing.add(chart)
    return drawing


def _executive_summary(data: dict[str, Any]) -> str:
    counts = data.get("risk_distribution", {})
    urgent = int(counts.get("critical", 0)) + int(counts.get("high", 0))
    risk_text = (
        f"Se identificaron {urgent} riesgo(s) crítico(s) o alto(s) que requieren priorización gerencial."
        if urgent
        else "No se registran riesgos críticos o altos; se recomienda mantener el monitoreo."
    )
    maturity_text = (
        f"La madurez NIST CSF 2.0 registrada es {float(data.get('maturity_percent', 0)):.1f}%."
        if data.get("answered_controls")
        else "Aún no hay respuestas suficientes para estimar la madurez NIST CSF 2.0."
    )
    return f"{_value(data.get('summary'))} {risk_text} {maturity_text}"


def build_pdf(path: Path, report_type: str, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    styles = _styles()
    generated_at = data.get("generated_at") or datetime.now(UTC)
    generated = (
        generated_at.astimezone(UTC).strftime("%d/%m/%Y · %H:%M UTC")
        if isinstance(generated_at, datetime)
        else _value(generated_at)
    )
    doc = BaseDocTemplate(
        str(path),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=21 * mm,
        bottomMargin=18 * mm,
        title=_value(data.get("title")),
        author="SecureCommerce Advisor",
        subject="Informe de ciberseguridad empresarial",
        keywords="ciberseguridad, NIST CSF 2.0, riesgos, activos, MIPYME",
    )
    cover_frame = Frame(
        22 * mm,
        24 * mm,
        164 * mm,
        249 * mm,
        id="cover",
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
    )
    body_frame = Frame(
        doc.leftMargin,
        doc.bottomMargin,
        doc.width,
        doc.height,
        id="body",
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
    )
    doc.addPageTemplates(
        [
            PageTemplate(id="Cover", frames=[cover_frame], onPage=lambda c, d: _cover(c, d, data)),
            PageTemplate(
                id="Body", frames=[body_frame], onPage=lambda c, d: _header_footer(c, d, data)
            ),
        ]
    )

    company = data.get("company", {})
    risks = list(data.get("risks", []))
    assets = list(data.get("assets", []))
    functions = list(data.get("maturity_functions", []))
    recommendations = list(data.get("recommendations", []))
    story: list[Any] = [
        Spacer(1, 78 * mm),
        Paragraph(
            "INFORME EJECUTIVO DE CIBERSEGURIDAD"
            if report_type == "executive"
            else "INFORME TÉCNICO DE CIBERSEGURIDAD",
            styles["eyebrow"],
        ),
        _p(data.get("title"), styles["cover_title"]),
        _p(data.get("organization"), styles["cover_org"]),
        Spacer(1, 10 * mm),
        Paragraph(
            f"<b>Alcance</b><br/>{escape(_value(data.get('scope')))}<br/><br/><b>Generado</b><br/>{escape(generated)}<br/><br/><b>Preparado por</b><br/>{escape(_value(data.get('prepared_by'), 'SecureCommerce Advisor'))}",
            styles["cover_meta"],
        ),
        Spacer(1, 42 * mm),
        Paragraph("CONFIDENCIAL · USO INTERNO", styles["eyebrow"]),
        NextPageTemplate("Body"),
        PageBreak(),
        Paragraph("Resumen ejecutivo", styles["h1"]),
        _p(_executive_summary(data), styles["body"]),
        Spacer(1, 3 * mm),
        _metric_cards(list(data.get("metrics", [])), styles),
        Paragraph("Perfil de la empresa", styles["h2"]),
        _table(
            [
                ["Dato", "Información", "Dato", "Información"],
                ["Razón social", data.get("organization"), "Sector", company.get("sector")],
                [
                    "Tamaño",
                    company.get("size"),
                    "País",
                    COUNTRIES.get(
                        _value(company.get("country"), "GT"), _value(company.get("country"))
                    ),
                ],
                [
                    "Código interno",
                    company.get("slug"),
                    "Estado",
                    "Activo" if company.get("is_active", True) else "Inactivo",
                ],
            ],
            [29 * mm, 50 * mm, 29 * mm, 50 * mm],
            styles,
        ),
        Paragraph("Panorama de riesgo", styles["h2"]),
        _risk_chart(dict(data.get("risk_distribution", {}))),
        Paragraph("Riesgos prioritarios", styles["h2"]),
    ]
    if risks:
        story.append(
            _table(
                [["Código y riesgo", "Nivel", "Inherente", "Residual", "Estado", "Avance"]]
                + [
                    [
                        f"{_value(risk.get('code'))} · {_value(risk.get('title'))}",
                        LEVELS.get(_enum(risk.get("level")), _enum(risk.get("level")).title()),
                        risk.get("score", 0),
                        risk.get("residual_score", 0),
                        STATUSES.get(_enum(risk.get("status")), _value(risk.get("status"))),
                        f"{risk.get('progress', 0)}%",
                    ]
                    for risk in risks[:10]
                ],
                [65 * mm, 20 * mm, 18 * mm, 18 * mm, 23 * mm, 16 * mm],
                styles,
            )
        )
    else:
        story.append(
            Paragraph("No hay riesgos registrados para el alcance seleccionado.", styles["body"])
        )

    story.extend(
        [
            PageBreak(),
            Paragraph("Madurez y controles", styles["h1"]),
            Paragraph(
                "Lectura basada en respuestas registradas para NIST CSF 2.0. El porcentaje expresa avance relativo sobre la escala configurada; no representa una certificación.",
                styles["body"],
            ),
            _maturity_chart(functions),
        ]
    )
    if functions:
        story.append(
            _table(
                [["Función", "Nombre", "Madurez", "Respuestas"]]
                + [
                    [
                        item.get("code"),
                        item.get("name"),
                        f"{float(item.get('percent', 0)):.1f}%",
                        item.get("answers", 0),
                    ]
                    for item in functions
                ],
                [24 * mm, 77 * mm, 29 * mm, 28 * mm],
                styles,
            )
        )
    story.append(Paragraph("Plan de acción priorizado", styles["h2"]))
    if recommendations:
        story.append(
            _table(
                [["Prioridad", "Acción recomendada", "Responsable", "Fecha objetivo", "Avance"]]
                + [
                    [
                        index,
                        item.get("action"),
                        item.get("responsible"),
                        item.get("target_date"),
                        f"{item.get('progress', 0)}%",
                    ]
                    for index, item in enumerate(recommendations[:8], 1)
                ],
                [15 * mm, 73 * mm, 28 * mm, 27 * mm, 17 * mm],
                styles,
            )
        )
    else:
        story.append(
            Paragraph(
                "No hay acciones de tratamiento registradas. Registre responsables, fechas objetivo y evidencia verificable para habilitar el seguimiento.",
                styles["body"],
            )
        )
    story.extend(
        [
            Paragraph("Activos críticos", styles["h2"]),
            Paragraph(
                "Priorizados por criticidad global de confidencialidad, integridad y disponibilidad.",
                styles["body"],
            ),
        ]
    )
    if assets:
        story.append(
            _table(
                [["Código", "Activo", "Tipo", "Responsable", "Exposición", "Crit."]]
                + [
                    [
                        asset.get("code"),
                        asset.get("name"),
                        ASSET_TYPES.get(_enum(asset.get("type")), _value(asset.get("type"))),
                        asset.get("owner"),
                        EXPOSURES.get(_enum(asset.get("exposure")), _value(asset.get("exposure"))),
                        f"{asset.get('criticality', 0)}/5",
                    ]
                    for asset in sorted(
                        assets, key=lambda item: int(item.get("criticality", 0)), reverse=True
                    )[:10]
                ],
                [24 * mm, 43 * mm, 31 * mm, 31 * mm, 20 * mm, 13 * mm],
                styles,
            )
        )
    else:
        story.append(
            Paragraph("No hay activos registrados para el alcance seleccionado.", styles["body"])
        )

    if report_type == "technical":
        story.extend(
            [
                PageBreak(),
                Paragraph("Anexo técnico", styles["h1"]),
                Paragraph("Metodología de riesgo", styles["h2"]),
                Paragraph(
                    "El puntaje inherente y residual se calcula como probabilidad × impacto en una matriz 5 × 5. La clasificación utiliza las bandas configuradas. La IA no modifica estos cálculos reproducibles.",
                    styles["body"],
                ),
                Paragraph("Detalle de riesgos", styles["h2"]),
            ]
        )
        for risk in risks:
            detail = [
                [
                    "Código",
                    risk.get("code"),
                    "Nivel",
                    LEVELS.get(_enum(risk.get("level")), risk.get("level")),
                ],
                [
                    "Riesgo",
                    risk.get("title"),
                    "Estado",
                    STATUSES.get(_enum(risk.get("status")), risk.get("status")),
                ],
                [
                    "Descripción",
                    risk.get("description"),
                    "Estrategia",
                    STRATEGIES.get(_enum(risk.get("strategy")), risk.get("strategy")),
                ],
                [
                    "Inherente",
                    f"P {risk.get('probability', 0)} × I {risk.get('impact', 0)} = {risk.get('score', 0)}",
                    "Residual",
                    f"P {risk.get('residual_probability', 0)} × I {risk.get('residual_impact', 0)} = {risk.get('residual_score', 0)}",
                ],
                ["Responsable", risk.get("responsible"), "Fecha objetivo", risk.get("target_date")],
                ["Controles", risk.get("controls"), "Avance", f"{risk.get('progress', 0)}%"],
            ]
            story.append(
                KeepTogether(
                    [
                        _table(detail, [31 * mm, 58 * mm, 30 * mm, 41 * mm], styles),
                        Spacer(1, 4 * mm),
                    ]
                )
            )

    story.extend(
        [
            PageBreak(),
            Paragraph("Trazabilidad y alcance", styles["h1"]),
            _table(
                [
                    ["Campo", "Valor"],
                    ["Identificador", data.get("report_id")],
                    ["Tipo", "Ejecutivo" if report_type == "executive" else "Técnico"],
                    ["Generado", generated],
                    [
                        "Registros considerados",
                        f"{data.get('asset_count', len(assets))} activos · {data.get('risk_count', len(risks))} riesgos · {data.get('answered_controls', 0)} respuestas",
                    ],
                    ["Evidencias registradas", data.get("evidence_count", 0)],
                    ["Marco", "NIST Cybersecurity Framework (CSF) 2.0"],
                ],
                [48 * mm, 112 * mm],
                styles,
            ),
            Paragraph("Interpretación responsable", styles["h2"]),
            Paragraph(
                "Este informe refleja exclusivamente la información registrada en SecureCommerce Advisor al momento de su generación. Los campos sin datos se muestran como “No registrado”; no se completan mediante suposiciones. Requiere revisión humana y no constituye certificación, auditoría externa, prueba de penetración, SOC ni sustituye un servicio de respuesta a incidentes.",
                styles["body"],
            ),
            Paragraph("Próxima revisión sugerida", styles["h2"]),
            Paragraph(
                "Actualizar el inventario, revisar riesgos críticos y altos, documentar responsables y fechas objetivo, adjuntar evidencias y volver a generar el reporte después de cada ciclo de seguimiento.",
                styles["body"],
            ),
        ]
    )
    doc.build(story)
