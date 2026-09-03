# Modelo de amenazas

## Alcance y límites de confianza

Activos principales: identidades, membresías, datos empresariales, evidencias, reportes, secretos, tokens y auditoría. Los límites son navegador–Nginx, Nginx–API, API/worker–PostgreSQL/Redis/almacenamiento y API–proveedor de IA. PostgreSQL y Redis permanecen en una red interna.

## Análisis STRIDE

| Amenaza | Escenario | Mitigación vigente | Riesgo residual |
|---|---|---|---|
| Suplantación | Robo o reutilización de sesión | Argon2id, MFA, JWT de 15 min, refresh rotativo/revocable y bloqueo | Medio: falta OIDC/WebAuthn |
| Manipulación | Cambio de organización, puntajes o PDF | Organización derivada de membresía, cálculo determinístico, Pydantic y SHA-256 | Bajo |
| Repudio | Negación de cambios o descargas | AuditLog con actor, organización, recurso, resultado, hora y correlación | Medio: log externo inmutable pendiente |
| Divulgación | Acceso cruzado, logs, IA o backups | Filtros tenant, permisos, minimización para IA, red interna y backup cifrado | Medio: S3/KMS pendiente |
| Denegación | Fuerza bruta o agotamiento | Bloqueo, rate limit, límites de IA y tareas asíncronas | Medio: falta autoscaling/WAF |
| Elevación | Rol insuficiente o token manipulado | RBAC central, denegación por defecto y membresía activa en backend | Bajo |

## Abuso específico

- Prompt injection: el texto se delimita como datos, se minimiza y la salida se valida; ninguna acción se aplica automáticamente.
- Evidencias: el MVP registra metadatos, no cargas binarias. Una carga futura debe validar firma MIME, tamaño, malware y ruta.
- SSRF: no existe descarga arbitraria de URL; integraciones futuras usarán destinos permitidos.
- Reportes: las rutas se resuelven dentro del almacenamiento configurado y se autorizan por organización.

Revisar este documento al cambiar un límite de confianza, proveedor, almacenamiento o autenticación.
