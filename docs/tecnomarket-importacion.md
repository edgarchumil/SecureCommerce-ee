# TecnoMarket GT, S.A.

Empresa incorporada desde `Proyecto Final Seguridad de Sistemas Informaticos.pdf`
(84 páginas, proyecto académico 2026). La carga reproduce el caso del documento;
no representa un descubrimiento de red ni una auditoría de infraestructura real.

## Contenido y trazabilidad

- 12 activos A01–A12: cuatro de producción, cuatro de pruebas y cuatro de desarrollo.
- 120 escenarios específicos de amenaza y 120 brechas, vinculados uno a uno con los riesgos.
- 120 riesgos R-A01-01–R-A12-10, con probabilidad, impacto, capa, dimensiones y página fuente.
- 120 acciones propuestas de tratamiento: 115 mitigar, 4 transferir y 1 aceptar.
- 28 críticos, 66 altos y 26 medios/moderados; ningún riesgo bajo.

El catálogo general AM-01–AM-15 de la página 18 agrupa amenazas por origen;
los registros de amenaza del sistema contienen los escenarios específicos de las
matrices de las páginas 20–38, para conservar el vínculo exacto con cada riesgo.
Los recursos humanos se representan como activos de tipo «Otro», con la etiqueta
`recurso-humano`; no se inventan nombres de empleados ni cuentas personales.

La matriz de esta empresa usa bajo 1–4, medio 5–9, alto 10–15 y crítico 16–25,
según las páginas 16–17. Los umbrales de las demás empresas se conservan.
Los valores C/I/D provienen de la página 12. El sistema calcula la criticidad global
como el máximo de C/I/D; las notas conservan también el promedio y nivel originales.

Todos los riesgos permanecen identificados, con avance 0%, sin fechas ni responsables
nominales inventados. Las acciones se presentan como propuestas del documento.
El residual se mantiene igual al inherente hasta verificar la eficacia de controles.
La decisión documental de aceptar un riesgo no se presenta como aceptación aprobada.
La valoración 1–5 de las brechas usa el impacto del riesgo; no se interpreta como CVSS.

Las páginas 55–56 documentan una réplica OWASP Juice Shop, no producción. OpenVAS
no produjo resultados de escaneo válidos. No se crean incidentes confirmados ni
respuestas NIST a partir de estas pruebas. El inventario declara datos sintéticos en
pruebas, pero la matriz plantea copias productivas: esta discrepancia se señala en
los activos A05 y A07 para su validación.

## Reproducción

El JSON conserva el SHA-256 del PDF. El extractor normaliza los identificadores
R-A1101–R-A1110 y corrige la fila desplazada R-A07-10 tras revisión visual del PDF.

```powershell
.venv/Scripts/python.exe -X utf8 tools/extract_tecnomarket.py "C:/ruta/Proyecto Final Seguridad de Sistemas Informaticos.pdf"
.venv/Scripts/python.exe -X utf8 tools/import_tecnomarket.py
.venv/Scripts/python.exe -X utf8 tools/import_tecnomarket.py --apply
```

La primera orden requiere PyMuPDF. La segunda solo valida datos, esquemas y
distribuciones por ambiente; la tercera aplica la carga mediante la API autenticada.
La API registra auditoría y persiste los datos en PostgreSQL de Render. El importador
se puede reanudar: reconoce activos, amenazas, brechas, riesgos y acciones existentes.
No elimina registros ni sobrescribe avances posteriores. Si estos cambian, la
verificación del estado inicial avisará que el resultado ya no coincide con la carga.

El registro existente exige una cuenta inicial diferente. La credencial aleatoria de
esa cuenta administrativa de bootstrap permanece exclusivamente en
`tmp/tecnomarket-bootstrap.json`, excluido de Git. La membresía del administrador
habitual se agrega mediante el endpoint interno, que no envía correo ni mensajes.
Se ingresa con `administrador@demo.local` y su contraseña habitual, seleccionando
**TecnoMarket GT, S.A.** en el selector o en **Mis empresas**.

La verificación de la nube queda en `output/tecnomarket/verificacion-nube.json`.
La aplicación se encuentra en https://securecommerce-ee.onrender.com.

## Verificación del 5 de septiembre de 2026

Se comprobó la persistencia mediante lecturas nuevas de la API, las 120 acciones,
el panel (12 activos, 120 riesgos y 94 prioritarios), búsqueda A12/R-A12-10,
paginación de riesgos, umbral crítico 16 y cambio de empresa hacia Maya y de regreso.
Las capturas de la interfaz desplegada se guardaron en `output/tecnomarket/`.
Los reportes ejecutivo (5 páginas) y técnico (51 páginas, 120 códigos de riesgo)
se generaron y descargaron desde la nube; también están en Reportes PDF.

La suite funcional del backend contiene 56 pruebas satisfactorias. Se configura
la concurrencia `thread, greenlet` para que Coverage mida también las continuaciones
de SQLAlchemy asíncrono; sin esta opción la medición omite código ejecutado.
Referencia: https://coverage.readthedocs.io/en/7.13.4/config.html#run-concurrency.
La interfaz superó pruebas de búsqueda/paginación, escala por empresa y limpieza
de caché, lint y compilación. La revisión del navegador no registró errores JavaScript.

Limitación previa del repositorio: el workflow independiente `Security` no arranca
porque `.github/workflows/security.yml` referencia una versión inexistente
`aquasecurity/trivy-action@0.33.1`. No es un resultado de escaneo ni impidió el
despliegue de Render. Su corrección no forma parte de la importación documental.
