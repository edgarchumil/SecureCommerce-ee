# Modelo de datos

La Fase 5 incorpora Threat, Vulnerability, Risk, RiskTreatment y SystemSetting. Risk enlaza un activo obligatorio y relaciones opcionales de la misma organización; conserva puntajes inherentes y residuales, estrategia, estado y avance. RiskTreatment registra múltiples acciones trazables y SystemSetting guarda rangos validados por organización.

La Fase 2 incorpora User, Organization, Membership, Role, Permission, Session y AuditLog con UUID, timestamps UTC, eliminación lógica donde corresponde, índices y restricciones. La membresía vincula el rol con una organización. Los refresh tokens solo se conservan como hashes SHA-256. La migración habilita RLS en membresías y auditoría como preparación; la API aplica siempre el filtro por organización independientemente de RLS.

La Fase 3 añade Asset y AssetDependency. El código interno es único dentro de cada organización; dependencias y consultas exigen la misma organización. La criticidad general es el máximo de confidencialidad, integridad y disponibilidad. Los activos utilizan eliminación lógica para preservar trazabilidad.

La Fase 4 incorpora Framework, FrameworkFunction, FrameworkCategory, FrameworkControl, Question, Evaluation, EvaluationAsset, Answer y Evidence. El catálogo es global y versionado; evaluaciones, respuestas y evidencias son multiempresa. La base conserva únicamente metadatos y hash de evidencias, nunca el archivo binario.

La Fase 10 incorpora Incident y Notification. Los incidentes conservan severidad, estado, fecha de ocurrencia y resolución, creador, organización y eliminación lógica. Las notificaciones están dirigidas simultáneamente a usuario y organización para impedir su exposición entre membresías.
