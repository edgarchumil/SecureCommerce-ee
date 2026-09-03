# API

La Fase 6 incorpora `GET /dashboard`, que devuelve KPIs y series agregadas con filtros opcionales `date_from`, `date_to` y `asset_type`. La respuesta se limita a la organización autenticada y no expone registros de detalle.

La Fase 5 añade `/threats`, `/vulnerabilities` y `/risks`, con búsqueda, filtros, paginación, CRUD y acciones en `/risks/{id}/treatments`. `PUT /settings/risk-bands` configura los rangos por organización y requiere rol administrador. Los puntajes se recalculan siempre en servidor.

La API REST se publica bajo `/api/v1`. En esta fase ofrece `GET /health/live` y `GET /health/ready`. OpenAPI está disponible en `/docs` y `/openapi.json`. Las respuestas incluyen `X-Correlation-ID`; el readiness devuelve 503 si una dependencia no está disponible.

La Fase 2 añade registro, login, refresh rotativo, logout, perfil, cambio y recuperación de contraseña, configuración/verificación MFA, organización actual, membresías, sesiones propias y auditoría. Los endpoints protegidos usan JWT Bearer; el refresh token viaja en cookie HttpOnly, SameSite Strict y Secure en producción. La recuperación devuelve el token únicamente en desarrollo; producción deberá entregarlo por un proveedor transaccional.

`/api/v1/assets` ofrece listado paginado, búsqueda, ordenamiento, filtros por tipo, estado y criticidad, creación, consulta, actualización y eliminación lógica. La organización nunca se toma del cuerpo de la solicitud.

`/api/v1/frameworks` expone catálogos y preguntas. `/api/v1/evaluations` crea evaluaciones con alcance y activos, autoguarda respuestas, registra metadatos de evidencia, controla estados y devuelve resultados ponderados por función y categoría. La clave de almacenamiento de evidencia se genera en backend y nunca se acepta desde el cliente.

La Fase 10 añade `/api/v1/users` como vista de las membresías de la organización, actualización de `/organizations/current`, CRUD tenant de `/incidents` y notificaciones propias en `/notifications`. Crear o modificar incidentes requiere permiso de escritura; usuarios de consulta solo pueden leer. Toda búsqueda de identificadores combina el UUID con la organización autenticada.
