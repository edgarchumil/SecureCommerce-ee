# Verificación de aceptación del MVP

La Fase 10 completa los flujos navegables de organización, usuarios/roles, perfil, MFA, recuperación, activos, evaluación NIST, riesgos y tratamientos, recomendaciones, dashboard, reportes, incidentes, auditoría, configuración y sesiones.

## Evidencia automatizada

- Pytest cubre cálculo determinístico, identidad, RBAC, aislamiento tenant, activos, evaluaciones, riesgos, IA, dashboard, PDF, incidentes y auditoría.
- Vitest cubre navegación protegida, formularios, dashboard, módulos principales y accesibilidad automatizada.
- Ruff, mypy, Bandit, pip-audit, npm audit, Gitleaks y Trivy forman la puerta de calidad.
- Docker Compose valida PostgreSQL, Redis, API, Celery, frontend, Nginx, migraciones, reportes y backup cifrado.

## Límites conscientes

El MVP no equivale a certificación NIST o ISO. En producción deben conectarse OIDC/correo transaccional, S3/KMS, Secrets Manager, TLS/WAF y observabilidad administrada. Las funciones fuera del MVP permanecen excluidas según el documento maestro.
