# ruff: noqa: E501
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def build_pdf(path: Path, report_type: str, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="CoverTitle",
            parent=styles["Title"],
            textColor=colors.HexColor("#0f2b46"),
            fontSize=26,
            leading=32,
            alignment=TA_CENTER,
            spaceAfter=16,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Section",
            parent=styles["Heading2"],
            textColor=colors.HexColor("#075985"),
            spaceBefore=12,
            spaceAfter=8,
        )
    )
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=str(data["title"]),
        author="SecureCommerce Advisor",
    )
    story = [
        Spacer(1, 40 * mm),
        Paragraph("SECURECOMMERCE ADVISOR", styles["Heading3"]),
        Paragraph(str(data["title"]), styles["CoverTitle"]),
        Paragraph(str(data["organization"]), styles["Heading2"]),
        Spacer(1, 8 * mm),
        Paragraph(f"Fecha: {datetime.now(UTC).date().isoformat()}", styles["Normal"]),
        Paragraph(f"Alcance: {data['scope']}", styles["Normal"]),
        PageBreak(),
    ]
    story.extend(
        [
            Paragraph("Resumen", styles["Section"]),
            Paragraph(str(data["summary"]), styles["BodyText"]),
            Paragraph("Indicadores", styles["Section"]),
        ]
    )
    metrics = [
        ["Indicador", "Valor"],
        *[[str(item["label"]), str(item["value"])] for item in data["metrics"]],
    ]
    table = Table(metrics, colWidths=[115 * mm, 45 * mm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f2b46")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    story.extend([table, Paragraph("Principales riesgos", styles["Section"])])
    for risk in data["risks"]:
        story.append(
            Paragraph(
                f"<b>{risk['code']} - {risk['title']}</b>: nivel {risk['level']}, puntaje {risk['score']}. Tratamiento: {risk['strategy']}.",
                styles["BodyText"],
            )
        )
        story.append(Spacer(1, 3 * mm))
    if report_type == "technical":
        story.extend(
            [
                PageBreak(),
                Paragraph("Metodología técnica", styles["Section"]),
                Paragraph(
                    "Los puntajes se calculan como probabilidad por impacto en una matriz 5 x 5. La IA no participa en el cálculo.",
                    styles["BodyText"],
                ),
                Paragraph("Inventario incluido", styles["Section"]),
            ]
        )
        for asset in data["assets"]:
            story.append(
                Paragraph(
                    f"{asset['code']} - {asset['name']} ({asset['type']}), criticidad {asset['criticality']}/5.",
                    styles["BodyText"],
                )
            )
    story.extend(
        [
            Paragraph("Recomendaciones prioritarias", styles["Section"]),
            Paragraph(
                "Revise los tratamientos pendientes, asigne responsables y conserve evidencia verificable. Este reporte no constituye una certificación.",
                styles["BodyText"],
            ),
        ]
    )

    def footer(canvas, document) -> None:  # type: ignore[no-untyped-def]
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#64748b"))
        canvas.drawString(18 * mm, 10 * mm, "SecureCommerce Advisor - Confidencial")
        canvas.drawRightString(192 * mm, 10 * mm, f"Página {document.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
