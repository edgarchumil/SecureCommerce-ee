# Reportes PDF

La Fase 8 genera reportes ejecutivos y técnicos mediante una tarea Celery. La API crea un trabajo pendiente y el worker construye el PDF con ReportLab, calcula SHA-256 y publica el archivo solo al finalizar.

Los reportes ejecutivos incluyen portada, organización, fecha, alcance, resumen, indicadores, riesgos y recomendaciones. Los técnicos añaden metodología e inventario. Todo reporte advierte que no constituye certificación.

Los archivos se almacenan en un volumen compartido fuera del contenido público. La clave se genera en backend, cada consulta exige la organización autenticada y la ruta se resuelve dentro del directorio permitido antes de descargar. Creación y descarga generan auditoría.
