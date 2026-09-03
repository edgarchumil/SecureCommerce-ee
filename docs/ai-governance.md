# Gobierno de inteligencia artificial

La Fase 7 incorpora recomendaciones asistidas para explicar y priorizar riesgos y preparar borradores de tratamiento. El cálculo de riesgo ocurre antes de cualquier llamada externa y nunca depende del modelo.

## Controles

- `AI_ENABLED=false` por defecto y fallback determinista siempre disponible.
- La interfaz `AIProvider` permite sustituir OpenAI por otro proveedor.
- OpenAI se consume mediante Responses API, Structured Outputs y `store=false`.
- Solo se envían códigos, tipos, puntajes, niveles y banderas; no se envían descripciones, evidencias, identidades, secretos ni tokens.
- Los datos se delimitan como no confiables y las instrucciones del sistema prohíben obedecer texto incluido en ellos.
- La respuesta se valida estrictamente con Pydantic y solo admite referencias NIST CSF 2.0, CIS Controls v8 u OWASP indicadas por el catálogo.
- Toda recomendación se marca como asistida y nace en estado borrador. Una persona puede editarla, aprobarla o rechazarla. Ninguna acción se aplica automáticamente.
- Se registran proveedor, modelo, versión del prompt, tokens, costo estimado, fecha, resultado y auditoría.
- El tiempo, salida máxima y presupuesto mensual son configurables. Ante clave ausente, función desactivada, presupuesto agotado, timeout, error HTTP o salida inválida se usa el fallback local.

## Costos

`AI_INPUT_COST_PER_MILLION` y `AI_OUTPUT_COST_PER_MILLION` deben configurarse con las tarifas contractuales vigentes de la organización. Permanecen en cero por defecto para evitar presentar estimaciones falsas. `AI_MONTHLY_BUDGET_LIMIT` impide nuevas llamadas externas cuando el costo registrado alcanza el límite.

## Limitaciones

Las recomendaciones no certifican cumplimiento, no prueban que un control exista y no sustituyen asesoría profesional. El catálogo inicial es deliberadamente limitado y debe mantenerse mediante revisión de seguridad.
