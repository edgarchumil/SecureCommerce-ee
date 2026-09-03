# Dashboard ejecutivo

La Fase 6 reúne indicadores de activos, madurez NIST y riesgos sin duplicar lógica de negocio en el navegador. `GET /api/v1/dashboard` calcula todos los agregados en el backend y aplica siempre el contexto de organización autenticado.

## Indicadores

- Total de activos dentro del filtro.
- Madurez NIST media como porcentaje de la escala 0–4.
- Riesgos abiertos y riesgos prioritarios (altos o críticos).
- Avance promedio de tratamientos.

El panel muestra distribuciones de activos por tipo, riesgos por nivel, evaluaciones por estado y riesgos identificados por mes. Puede filtrarse por fechas y tipo de activo; un rango invertido se rechaza.

## Accesibilidad y estados

Las gráficas incluyen nombre accesible y una tabla equivalente disponible para tecnologías de asistencia. Los controles tienen etiquetas, el foco conserva alto contraste y existen estados explícitos de carga, error y ausencia de datos. Los colores complementan etiquetas y valores; nunca son la única forma de comunicar el nivel.
