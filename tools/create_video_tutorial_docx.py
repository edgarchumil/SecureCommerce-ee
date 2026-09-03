from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "Tutorial_video_SecureCommerce_Advisor.docx"

BLUE = "2E74B5"
DARK = "0B2545"
MID = "1F4D78"
PALE = "E8EEF5"
LIGHT = "F4F6F9"
GOLD = "7A5A00"
MUTED = "5B6573"
WHITE = "FFFFFF"


def set_cell_shading(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_width(cell, dxa):
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_w = tc_pr.find(qn("w:tcW"))
    if tc_w is None:
        tc_w = OxmlElement("w:tcW")
        tc_pr.append(tc_w)
    tc_w.set(qn("w:w"), str(dxa))
    tc_w.set(qn("w:type"), "dxa")


def set_cell_margins(cell, top=80, start=120, bottom=80, end=120):
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for side, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{side}"))
        if node is None:
            node = OxmlElement(f"w:{side}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def fixed_table(table, widths):
    table.autofit = False
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    tbl_pr = table._tbl.tblPr
    tbl_w = tbl_pr.find(qn("w:tblW"))
    if tbl_w is None:
        tbl_w = OxmlElement("w:tblW")
        tbl_pr.append(tbl_w)
    tbl_w.set(qn("w:w"), "9360")
    tbl_w.set(qn("w:type"), "dxa")
    tbl_ind = tbl_pr.find(qn("w:tblInd"))
    if tbl_ind is None:
        tbl_ind = OxmlElement("w:tblInd")
        tbl_pr.append(tbl_ind)
    tbl_ind.set(qn("w:w"), "120")
    tbl_ind.set(qn("w:type"), "dxa")
    grid = table._tbl.tblGrid
    for child in list(grid):
        grid.remove(child)
    for width in widths:
        col = OxmlElement("w:gridCol")
        col.set(qn("w:w"), str(width))
        grid.append(col)
    for row in table.rows:
        tr_pr = row._tr.get_or_add_trPr()
        cant_split = OxmlElement("w:cantSplit")
        tr_pr.append(cant_split)
        for idx, cell in enumerate(row.cells):
            set_cell_width(cell, widths[idx])
            set_cell_margins(cell)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def set_repeat_table_header(row):
    tr_pr = row._tr.get_or_add_trPr()
    node = OxmlElement("w:tblHeader")
    node.set(qn("w:val"), "true")
    tr_pr.append(node)


def add_numbering(doc, ordered=True):
    part = doc.part.numbering_part
    root = part.element
    existing = [int(x.get(qn("w:abstractNumId"))) for x in root.findall(qn("w:abstractNum"))]
    abstract_id = max(existing, default=-1) + 1
    abstract = OxmlElement("w:abstractNum")
    abstract.set(qn("w:abstractNumId"), str(abstract_id))
    lvl = OxmlElement("w:lvl"); lvl.set(qn("w:ilvl"), "0")
    start = OxmlElement("w:start"); start.set(qn("w:val"), "1"); lvl.append(start)
    num_fmt = OxmlElement("w:numFmt"); num_fmt.set(qn("w:val"), "decimal" if ordered else "bullet"); lvl.append(num_fmt)
    lvl_text = OxmlElement("w:lvlText"); lvl_text.set(qn("w:val"), "%1." if ordered else "•"); lvl.append(lvl_text)
    suff = OxmlElement("w:suff"); suff.set(qn("w:val"), "tab"); lvl.append(suff)
    ppr = OxmlElement("w:pPr")
    tabs = OxmlElement("w:tabs"); tab = OxmlElement("w:tab"); tab.set(qn("w:val"), "num"); tab.set(qn("w:pos"), "540"); tabs.append(tab); ppr.append(tabs)
    ind = OxmlElement("w:ind"); ind.set(qn("w:left"), "540"); ind.set(qn("w:hanging"), "270"); ppr.append(ind)
    spacing = OxmlElement("w:spacing"); spacing.set(qn("w:after"), "80"); spacing.set(qn("w:line"), "300"); spacing.set(qn("w:lineRule"), "auto"); ppr.append(spacing)
    lvl.append(ppr)
    abstract.append(lvl)
    root.append(abstract)
    nums = [int(x.get(qn("w:numId"))) for x in root.findall(qn("w:num"))]
    num_id = max(nums, default=0) + 1
    num = OxmlElement("w:num"); num.set(qn("w:numId"), str(num_id))
    aid = OxmlElement("w:abstractNumId"); aid.set(qn("w:val"), str(abstract_id)); num.append(aid)
    root.append(num)
    return num_id


def list_item(doc, text, num_id):
    p = doc.add_paragraph()
    p_pr = p._p.get_or_add_pPr()
    num_pr = OxmlElement("w:numPr")
    ilvl = OxmlElement("w:ilvl"); ilvl.set(qn("w:val"), "0")
    num = OxmlElement("w:numId"); num.set(qn("w:val"), str(num_id))
    num_pr.append(ilvl); num_pr.append(num); p_pr.append(num_pr)
    p.add_run(text)
    return p


def add_heading(doc, text, level=1):
    return doc.add_heading(text, level=level)


def add_callout(doc, title, text, fill=LIGHT):
    table = doc.add_table(rows=1, cols=1)
    fixed_table(table, [9360])
    cell = table.cell(0, 0); set_cell_shading(cell, fill)
    p = cell.paragraphs[0]
    r = p.add_run(title + "  "); r.bold = True; r.font.color.rgb = RGBColor.from_string(DARK)
    p.add_run(text)
    doc.add_paragraph().paragraph_format.space_after = Pt(0)


def add_scene_table(doc, rows):
    table = doc.add_table(rows=1, cols=4)
    table.style = "Table Grid"
    headers = ["Tiempo", "Pantalla / acción", "Narración sugerida", "Clave visual"]
    for idx, text in enumerate(headers):
        cell = table.rows[0].cells[idx]; set_cell_shading(cell, PALE)
        run = cell.paragraphs[0].add_run(text); run.bold = True; run.font.color.rgb = RGBColor.from_string(DARK)
    for values in rows:
        cells = table.add_row().cells
        for idx, text in enumerate(values):
            cells[idx].text = text
    fixed_table(table, [1100, 2150, 4210, 1900])
    set_repeat_table_header(table.rows[0])
    return table


def set_page_field(paragraph):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = paragraph.add_run("Página ")
    run.font.size = Pt(9); run.font.color.rgb = RGBColor.from_string(MUTED)
    fld = OxmlElement("w:fldSimple"); fld.set(qn("w:instr"), "PAGE")
    paragraph._p.append(fld)


def build():
    doc = Document()
    sec = doc.sections[0]
    sec.page_width = Inches(8.5); sec.page_height = Inches(11)
    sec.top_margin = sec.bottom_margin = sec.left_margin = sec.right_margin = Inches(1)
    sec.header_distance = sec.footer_distance = Inches(0.492)

    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Calibri"; normal.font.size = Pt(11); normal.font.color.rgb = RGBColor(25, 33, 45)
    normal.paragraph_format.space_before = Pt(0); normal.paragraph_format.space_after = Pt(6); normal.paragraph_format.line_spacing = 1.25
    for name, size, color, before, after in (
        ("Heading 1", 16, BLUE, 18, 10), ("Heading 2", 13, BLUE, 14, 7), ("Heading 3", 12, MID, 10, 5)
    ):
        st = styles[name]; st.font.name = "Calibri"; st.font.size = Pt(size); st.font.bold = True; st.font.color.rgb = RGBColor.from_string(color)
        st.paragraph_format.space_before = Pt(before); st.paragraph_format.space_after = Pt(after); st.paragraph_format.keep_with_next = True

    header = sec.header.paragraphs[0]
    header.text = "SECURECOMMERCE ADVISOR  |  GUION DE DEMOSTRACIÓN"
    header.runs[0].font.size = Pt(8.5); header.runs[0].font.bold = True; header.runs[0].font.color.rgb = RGBColor.from_string(MUTED)
    set_page_field(sec.footer.paragraphs[0])

    ordered = add_numbering(doc, True); bullets = add_numbering(doc, False)

    # First-page workshop agenda pattern.
    p = doc.add_paragraph(); p.paragraph_format.space_before = Pt(8); p.paragraph_format.space_after = Pt(0)
    r = p.add_run("TUTORIAL DE PRESENTACIÓN EN VIDEO"); r.bold = True; r.font.size = Pt(10); r.font.color.rgb = RGBColor.from_string(BLUE)
    p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(8)
    r = p.add_run("Cómo presentar SecureCommerce Advisor desde cero"); r.bold = True; r.font.size = Pt(29); r.font.color.rgb = RGBColor.from_string(DARK)
    p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(18)
    r = p.add_run("Guion práctico para grabar una demostración clara, profesional y segura del sistema local."); r.font.size = Pt(13.2); r.font.color.rgb = RGBColor.from_string(MUTED)
    metrics = doc.add_table(rows=1, cols=4); metrics.style = "Table Grid"
    for i, (a, b) in enumerate((("9 min", "Video completo"), ("5 min", "Versión corta"), ("1080p", "Entrega recomendada"), ("1 persona", "Presentador"))):
        cell = metrics.cell(0, i); set_cell_shading(cell, "FFF8E8")
        p = cell.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        rr = p.add_run(a + "\n"); rr.bold = True; rr.font.size = Pt(14); rr.font.color.rgb = RGBColor.from_string(GOLD)
        rr = p.add_run(b); rr.font.size = Pt(8.5); rr.font.color.rgb = RGBColor.from_string(DARK)
    fixed_table(metrics, [2340] * 4)

    add_heading(doc, "Resultado que vas a producir", 1)
    doc.add_paragraph("Al terminar tendrás un video MP4 de demostración, con narración y subtítulos, que explica el problema, la solución, el flujo principal y el valor de SecureCommerce Advisor. Este documento funciona como lista de preparación, guion y control de calidad.")
    add_callout(doc, "Regla de oro.", "Graba con datos ficticios. Nunca muestres el archivo .env, claves API, tokens, secretos MFA, registros internos ni credenciales reales.", "FFF4E5")

    add_heading(doc, "1. Define la presentación antes de grabar", 1)
    for item in (
        "Público: docentes, posibles clientes, equipo técnico o dirección.",
        "Objetivo: demostrar cómo una MIPYME identifica activos, evalúa su postura NIST, prioriza riesgos y obtiene acciones y reportes.",
        "Mensaje central: la plataforma convierte información técnica en decisiones comprensibles, sin afirmar que certifica cumplimiento.",
        "Formato recomendado: video de 8 a 9 minutos; deja 30 segundos adicionales para créditos o contacto.",
    ): list_item(doc, item, bullets)

    add_heading(doc, "2. Prepara el sistema y el escritorio", 1)
    prep = (
        "Abre Docker Desktop y espera a que indique que el motor está activo.",
        "En PowerShell, dentro del proyecto, ejecuta docker compose up -d --build.",
        "Verifica con docker compose ps: los servicios principales deben aparecer activos o saludables.",
        "Abre http://localhost:8080 y confirma que la página de inicio carga.",
        "Cierra correo, mensajería y pestañas privadas; desactiva notificaciones.",
        "Usa una ventana del navegador limpia, zoom de 100 % y resolución de 1920 × 1080.",
        "Prepara una carpeta para grabaciones, imágenes, música autorizada y exportaciones.",
        "Haz un recorrido de ensayo completo y anota cualquier pantalla que tarde en cargar.",
    )
    for item in prep: list_item(doc, item, ordered)

    add_heading(doc, "Acceso de demostración", 2)
    table = doc.add_table(rows=1, cols=3); table.style = "Table Grid"
    for i, h in enumerate(("Rol", "Usuario", "Uso durante la demo")):
        c = table.rows[0].cells[i]; set_cell_shading(c, PALE); rr = c.paragraphs[0].add_run(h); rr.bold = True
    for row in (("Administrador", "administrador@demo.local", "Recorrido completo"), ("Analista", "analista@demo.local", "Evaluaciones y análisis"), ("Consulta", "consulta@demo.local", "Vista de solo consulta")):
        cells = table.add_row().cells
        for i, value in enumerate(row): cells[i].text = value
    fixed_table(table, [1800, 3240, 4320]); set_repeat_table_header(table.rows[0])
    doc.add_paragraph("Contraseña local actual: SceDemo_2026_Local_4mK8. Es exclusiva del entorno de demostración. Si el video será público, no la escribas en pantalla: pega la contraseña con la grabación pausada o reemplázala antes de publicar.")

    add_heading(doc, "3. Configura la grabación", 1)
    for item in (
        "Captura: selecciona únicamente la ventana del navegador; evita grabar todo el escritorio.",
        "Video: 1920 × 1080, 30 fps y cursor visible.",
        "Audio: micrófono a 10–15 cm, habitación silenciosa y prueba de 20 segundos.",
        "Cámara: opcional; si la usas, colócala en una esquina que no tape botones ni gráficos.",
        "Ritmo: mueve el cursor despacio, deja 1–2 segundos antes de cada clic y evita desplazamientos bruscos.",
        "Método: graba por escenas. Es más fácil repetir 45 segundos que rehacer nueve minutos.",
    ): list_item(doc, item, bullets)

    add_heading(doc, "4. Guion completo del video", 1)
    doc.add_paragraph("Duración objetivo: 8:30–9:00. Lee la narración con naturalidad; no memorices palabra por palabra.")
    add_scene_table(doc, [
        ("0:00–0:25", "Portada con nombre del sistema y subtítulo.", "Hoy veremos cómo SecureCommerce Advisor ayuda a una MIPYME a conocer sus activos, evaluar su postura de ciberseguridad y priorizar acciones concretas.", "Título grande; música suave opcional."),
        ("0:25–0:55", "Página de inicio en localhost:8080.", "La plataforma centraliza inventario, evaluaciones basadas en NIST CSF 2.0, riesgos, recomendaciones y reportes en un único espacio.", "Señala las cuatro capacidades."),
        ("0:55–1:20", "Abrir Ingresar; completar usuario administrador. Pausar antes de la contraseña.", "Ingresamos con una cuenta de demostración. El sistema usa roles para limitar las acciones disponibles a cada persona.", "No revelar la contraseña."),
        ("1:20–2:10", "Panel: recorrer indicadores, gráficos, filtros y tarjetas de módulos.", "El panel ofrece una vista ejecutiva: activos, evaluaciones y riesgos. Los filtros permiten concentrarse en fechas o tipos de activo sin perder el contexto general.", "Zoom lento sobre KPIs y gráficos."),
        ("2:10–2:55", "Abrir Inventario de activos; mostrar lista y formulario de nuevo activo sin guardar datos sensibles.", "El inventario registra aquello que la empresa necesita proteger: servidores, equipos, aplicaciones, información, servicios en la nube y proveedores.", "Usar únicamente datos ficticios."),
        ("2:55–3:55", "Volver al panel; abrir Evaluación NIST; mostrar evaluaciones, cuestionario y resultados existentes.", "Las evaluaciones organizan preguntas según NIST CSF 2.0. El resultado permite comparar el estado actual con el objetivo e identificar brechas prioritarias.", "No completar todo en vivo; usa un resultado ya creado."),
        ("3:55–4:45", "Abrir Gestión de riesgos; mostrar matriz o lista, nivel y tratamiento.", "Los hallazgos se convierten en riesgos valorados. Esto ayuda a decidir qué atender primero, quién es responsable y qué tratamiento requiere seguimiento.", "Destacar prioridad, no solo cantidad."),
        ("4:45–5:40", "Abrir Recomendaciones; elegir un riesgo y generar borrador si el flujo está listo.", "La asistencia genera un borrador de tratamiento, pero ninguna acción se aplica automáticamente. Una persona debe editar, aprobar o rechazar cada recomendación.", "Enfatizar supervisión humana."),
        ("5:40–6:20", "Abrir Incidentes; mostrar registro y seguimiento.", "El módulo de incidentes concentra eventos de seguridad para darles seguimiento y conectarlos con la operación de la organización.", "Evitar detalles reales de incidentes."),
        ("6:20–6:55", "Abrir Auditoría y luego Sesiones activas.", "Las acciones sensibles dejan trazabilidad, y las sesiones pueden revisarse o revocarse. Esto refuerza el control operativo del acceso.", "No mostrar tokens ni información técnica privada."),
        ("6:55–7:55", "Abrir Reportes PDF; crear reporte ejecutivo con título y alcance ficticios; esperar estado completado y descargar.", "Finalmente, generamos reportes ejecutivos o técnicos. El trabajo se procesa en segundo plano y, al completarse, el documento puede descargarse para comunicar resultados.", "Título sugerido: Resumen de ciberseguridad demo."),
        ("7:55–8:35", "Regresar al panel y mostrar Cumplimiento NIST.", "SecureCommerce Advisor reúne el ciclo completo: conocer, evaluar, priorizar, actuar y comunicar. Es una herramienta de apoyo; no sustituye el criterio profesional ni constituye una certificación.", "Cerrar con cinco verbos en pantalla."),
        ("8:35–8:55", "Diapositiva final con URL local o datos de contacto.", "Gracias por acompañarme. La demostración se ejecutó localmente con información ficticia y un entorno aislado.", "Fundido a negro de 1 segundo."),
    ])

    add_heading(doc, "5. Ruta exacta de clics", 1)
    clicks = (
        "Inicio → Ingresar → cuenta Administrador.",
        "Panel → revisar KPIs → cambiar Tipo de activo → Limpiar filtros.",
        "Inventario de activos → Nuevo activo → mostrar campos → cancelar o volver.",
        "Panel → Evaluación NIST → abrir una evaluación existente → cuestionario → resultados.",
        "Panel → Gestión de riesgos → abrir o señalar un riesgo prioritario.",
        "Panel → Recomendaciones asistidas → seleccionar riesgo → Generar borrador → revisar opciones Editar, Aprobar y Rechazar.",
        "Panel → Incidentes → mostrar estados de seguimiento.",
        "Panel → Auditoría → volver → Sesiones activas.",
        "Panel → Reportes PDF → Ejecutivo → título y alcance → Generar reporte → Descargar cuando esté completado.",
        "Panel → Cumplimiento NIST → cierre.",
    )
    for item in clicks: list_item(doc, item, ordered)

    add_heading(doc, "6. Graba, edita y exporta", 1)
    for item in (
        "Haz una prueba de 20 segundos y confirma que voz, cursor y texto se distinguen.",
        "Graba cada bloque del guion dejando 2 segundos de silencio al inicio y al final.",
        "Recorta errores y esperas largas; acelera solo cargas sin narración.",
        "Añade rótulos breves para cada módulo y difumina cualquier dato que no sea ficticio.",
        "Normaliza la voz para que se escuche uniforme; la música, si existe, debe quedar muy por debajo de la narración.",
        "Genera subtítulos y corrige manualmente nombres como SecureCommerce Advisor, NIST CSF 2.0 y MIPYME.",
        "Exporta MP4 con H.264, 1920 × 1080, 30 fps, audio AAC y tasa aproximada de 8–12 Mbps.",
        "Reproduce el archivo completo fuera del editor antes de compartirlo.",
    ): list_item(doc, item, ordered)

    add_heading(doc, "7. Versión rápida de cinco minutos", 1)
    compact = doc.add_table(rows=1, cols=2); compact.style = "Table Grid"
    for i, h in enumerate(("Tiempo", "Contenido")):
        c = compact.rows[0].cells[i]; set_cell_shading(c, PALE); c.paragraphs[0].add_run(h).bold = True
    for a, b in (("0:00–0:30", "Problema y propuesta de valor"), ("0:30–1:20", "Ingreso y panel"), ("1:20–2:05", "Activos"), ("2:05–3:05", "Evaluación NIST y resultados"), ("3:05–3:50", "Riesgos y recomendaciones supervisadas"), ("3:50–4:30", "Reporte PDF"), ("4:30–5:00", "Seguridad, límites y cierre")):
        cells = compact.add_row().cells; cells[0].text = a; cells[1].text = b
    fixed_table(compact, [1800, 7560]); set_repeat_table_header(compact.rows[0])

    add_heading(doc, "8. Si prefieres diapositivas", 1)
    slides = (
        "Portada: SecureCommerce Advisor.", "Problema: ciberseguridad difícil de priorizar en MIPYMES.",
        "Solución: plataforma centralizada y multiempresa.", "Arquitectura: interfaz web, API, base de datos, cola de tareas y proxy.",
        "Flujo: activos → evaluación → riesgos → tratamiento → reporte.", "Panel ejecutivo y filtros.",
        "NIST CSF 2.0 y cumplimiento.", "Recomendaciones con revisión humana.",
        "Seguridad: roles, sesiones, auditoría y datos ficticios.", "Cierre: beneficios, límites y próximos pasos.",
    )
    for item in slides: list_item(doc, item, ordered)
    doc.add_paragraph("Consejo: usa una idea por diapositiva, poco texto y una captura grande. La explicación debe estar en tu voz, no escrita completa en la pantalla.")

    add_heading(doc, "9. Plan de contingencia para una demostración en vivo", 1)
    for item in (
        "Ten el video exportado como respaldo, incluso si planeas presentar en vivo.",
        "Guarda capturas del panel, resultados NIST, riesgos y reporte final.",
        "Abre previamente las páginas que vas a mostrar y conserva una copia del PDF.",
        "Si un reporte tarda, explica que se genera en segundo plano y continúa con el siguiente módulo.",
        "Si falla la red, recuerda que la demostración local depende de Docker, no de una publicación externa; las funciones de IA pueden operar en modo local según la configuración.",
    ): list_item(doc, item, bullets)

    add_heading(doc, "10. Control de calidad final", 1)
    checks = (
        "La aplicación aparece nítida y sin barras innecesarias.", "La voz se entiende con auriculares y altavoces.",
        "No aparecen contraseñas, .env, claves, tokens ni información personal.", "Todos los datos mostrados son ficticios.",
        "Los subtítulos coinciden con la narración.", "No hay silencios largos ni clics confusos.",
        "El reporte descargado abre correctamente.", "La conclusión menciona el valor y también el límite de no certificación.",
        "El archivo tiene un nombre claro, por ejemplo SecureCommerce_Advisor_Demo_v1.mp4.",
    )
    for item in checks: list_item(doc, "☐ " + item, bullets)

    add_callout(doc, "Frase final sugerida.", "SecureCommerce Advisor permite pasar de datos dispersos a decisiones de ciberseguridad priorizadas, trazables y fáciles de comunicar.", PALE)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    print(OUT)


if __name__ == "__main__":
    build()
