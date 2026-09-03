from pathlib import Path
import subprocess
import wave

from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
import win32com.client


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs" / "video_securecommerce"
SCREENS = BASE / "screens"
AUDIO = BASE / "audio"
SEGMENTS = BASE / "segments"
OUT = ROOT / "docs" / "Video_presentacion_SecureCommerce_Advisor.mp4"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

SCENES = [
    ("00_portada.png", "SecureCommerce Advisor", "Ciberseguridad clara para MIPYMES", "Bienvenido a esta demostración de SecureCommerce Advisor, una plataforma que ayuda a pequeñas y medianas empresas a conocer sus activos, evaluar su postura de ciberseguridad y priorizar decisiones concretas."),
    ("01_inicio.png", "Una visión centralizada", "Activos, NIST, riesgos y reportes", "La solución reúne en un solo espacio el inventario de activos, evaluaciones basadas en NIST CSF dos punto cero, gestión de riesgos, recomendaciones supervisadas, incidentes, auditoría y reportes."),
    ("02_login.png", "Acceso controlado", "Usuarios, roles y sesiones", "El acceso se realiza mediante cuentas con roles definidos. Para esta demostración utilizamos una cuenta local ficticia de administrador. La contraseña se introduce de manera privada y no aparece en la grabación."),
    ("03_panel.png", "Panel ejecutivo", "Indicadores, gráficos y filtros", "Después de ingresar encontramos el panel ejecutivo. Aquí se resumen activos, evaluaciones y riesgos. Los filtros permiten analizar periodos o tipos de activo, mientras los gráficos facilitan explicar la situación a una persona no técnica."),
    ("04_activos.png", "Inventario de activos", "Qué necesita proteger la empresa", "El inventario registra lo que la organización necesita proteger: equipos, servidores, aplicaciones, información, servicios en la nube, cuentas críticas y proveedores. Cada registro incorpora estado y criticidad para apoyar la priorización."),
    ("05_evaluaciones.png", "Evaluación NIST CSF 2.0", "Estado actual y brechas prioritarias", "Las evaluaciones organizan el diagnóstico con el marco NIST CSF dos punto cero. Desde esta pantalla se abre el cuestionario y se consultan resultados. Así se compara el estado actual con el objetivo y se identifican brechas."),
    ("06_riesgos.png", "Gestión de riesgos", "Probabilidad, impacto y tratamiento", "Los hallazgos se convierten en riesgos valorados. La matriz de cinco por cinco combina probabilidad e impacto. La lista muestra riesgo inherente, riesgo residual, avance y estado, ayudando a decidir qué atender primero."),
    ("07_recomendaciones.png", "Recomendaciones asistidas", "La decisión siempre permanece en manos humanas", "Para un riesgo seleccionado, el sistema puede generar un borrador de tratamiento. El contenido asistido debe revisarse: una persona puede editarlo, aprobarlo o rechazarlo. Ninguna acción se ejecuta automáticamente."),
    ("08_incidentes.png", "Gestión de incidentes", "Registro y seguimiento operativo", "El módulo de incidentes permite documentar eventos de seguridad, asignar una severidad y seguir su evolución desde abierto hasta resuelto. En una demostración pública siempre deben utilizarse datos ficticios."),
    ("09_auditoria.png", "Trazabilidad", "Auditoría de acciones sensibles", "El historial de auditoría conserva la fecha, la acción, el recurso afectado y el resultado. Esta trazabilidad ayuda a comprender quién hizo qué y facilita las revisiones operativas."),
    ("10_reportes.png", "Reportes PDF", "Comunicación ejecutiva y técnica", "Los reportes pueden ser ejecutivos o técnicos. Se indica un título y un alcance; el trabajo se procesa en segundo plano y, cuando está completado, el documento queda disponible para descargar y compartir."),
    ("11_cumplimiento.png", "Ciclo completo", "Conocer, evaluar, priorizar, actuar y comunicar", "SecureCommerce Advisor conecta el ciclo completo: conocer los activos, evaluar controles, priorizar riesgos, proponer tratamientos y comunicar resultados. Es una herramienta de apoyo y no constituye una certificación."),
    ("12_cierre.png", "SecureCommerce Advisor", "Decisiones de ciberseguridad claras y trazables", "En resumen, la plataforma transforma información dispersa en decisiones de ciberseguridad priorizadas, trazables y fáciles de comunicar. Gracias por acompañarnos en esta demostración."),
]


def font(size, bold=False):
    names = ["C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"]
    return ImageFont.truetype(names[0], size)


def title_card(path, title, subtitle):
    image = Image.new("RGB", (1920, 1080), "#F8FAFC")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((160, 160, 1760, 920), radius=36, fill="#FFFFFF", outline="#CBD5E1", width=3)
    draw.rounded_rectangle((160, 160, 215, 920), radius=20, fill="#0B2545")
    draw.text((300, 390), title, font=font(68, True), fill="#0B2545")
    draw.text((305, 500), subtitle, font=font(34), fill="#475569")
    draw.text((305, 675), "Demostración local · Datos ficticios", font=font(24), fill="#2E74B5")
    image.save(path)


def overlay(path, title, subtitle):
    image = Image.open(path).convert("RGB")
    draw = ImageDraw.Draw(image, "RGBA")
    draw.rounded_rectangle((70, 790, 1220, 1010), radius=26, fill=(11, 37, 69, 235))
    draw.text((115, 830), title, font=font(45, True), fill="white")
    draw.text((118, 900), subtitle, font=font(27), fill="#DDEBFA")
    image.save(path)


def speak(text, path):
    speaker = win32com.client.Dispatch("SAPI.SpVoice")
    speaker.Rate = -1
    stream = win32com.client.Dispatch("SAPI.SpFileStream")
    stream.Open(str(path), 3, False)
    speaker.AudioOutputStream = stream
    speaker.Speak(text)
    stream.Close()


def duration(path):
    with wave.open(str(path), "rb") as f:
        return f.getnframes() / f.getframerate()


def run(args):
    subprocess.run(args, check=True)


def main():
    AUDIO.mkdir(parents=True, exist_ok=True)
    SEGMENTS.mkdir(parents=True, exist_ok=True)
    title_card(SCREENS / "00_portada.png", SCENES[0][1], SCENES[0][2])
    title_card(SCREENS / "12_cierre.png", SCENES[-1][1], SCENES[-1][2])
    for filename, title, subtitle, _ in SCENES[1:-1]:
        overlay(SCREENS / filename, title, subtitle)

    concat_lines = []
    for idx, (filename, _, _, narration) in enumerate(SCENES):
        wav = AUDIO / f"{idx:02d}.wav"
        mp4 = SEGMENTS / f"{idx:02d}.mp4"
        speak(narration, wav)
        seconds = duration(wav) + 1.2
        run([
            FFMPEG, "-y", "-loop", "1", "-i", str(SCREENS / filename), "-i", str(wav),
            "-vf", "scale=1920:1080,format=yuv420p,fade=t=in:st=0:d=0.4,fade=t=out:st=" + str(max(seconds - 0.5, 0)) + ":d=0.5",
            "-af", "afade=t=in:st=0:d=0.25,afade=t=out:st=" + str(max(seconds - 0.45, 0)) + ":d=0.45",
            "-t", f"{seconds:.3f}", "-r", "30", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
            "-c:a", "aac", "-b:a", "160k", "-shortest", str(mp4),
        ])
        concat_lines.append(f"file '{mp4.as_posix()}'")
    concat = BASE / "concat.txt"
    concat.write_text("\n".join(concat_lines), encoding="utf-8")
    run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy", "-movflags", "+faststart", str(OUT)])
    print(OUT)


if __name__ == "__main__":
    main()
