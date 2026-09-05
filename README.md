# SecureCommerce Advisor

**Estado actual: Fase 10 de cierre funcional completada.** El MVP incluye identidad, organizaciones, usuarios y roles, activos, NIST CSF 2.0, riesgos, incidentes, dashboard, recomendaciones asistidas, reportes PDF, auditoría y controles de calidad y seguridad.

Plataforma SaaS multiempresa de ciberseguridad para MIPYMES guatemaltecas. La base funcional del MVP puede ejecutarse completamente con Docker Compose.

## Requisitos

- Docker Desktop con Docker Compose v2.
- Git.
- Opcional para desarrollo sin contenedores: Python 3.12+ y Node.js 22+.

## Inicio rápido con Docker

```bash
cp .env.example .env
docker compose up --build
```

En PowerShell, use `Copy-Item .env.example .env` en lugar de `cp`.

- Aplicación: <http://localhost:8080>
- OpenAPI: <http://localhost:8080/docs>
- Liveness: <http://localhost:8080/api/v1/health/live>
- Readiness: <http://localhost:8080/api/v1/health/ready>
- Acceso: <http://localhost:8080/login>
- Registro de una nueva MIPYME: <http://localhost:8080/registro>

Detener: `docker compose down`. Para eliminar también datos locales: `docker compose down -v` (acción destructiva).

## Variables de entorno

Copie `.env.example` a `.env`. Cambie siempre `SECRET_KEY` y `POSTGRES_PASSWORD`. `.env` está excluido de Git. Las variables de IA están reservadas para la Fase 7 y `AI_ENABLED=false` por defecto.

`APP_PORT` permite cambiar el puerto público, por ejemplo `APP_PORT=8081`. PostgreSQL y Redis no publican puertos al host.

## Migraciones

Ejecute la migración de identidad:

```bash
docker compose run --rm api alembic upgrade head
```

Seed reproducible de identidad (la contraseña procede de `DEMO_PASSWORD`):

```bash
docker compose run --rm api python -m app.seed
```

## Pruebas y calidad

```bash
docker build --target test -t securecommerce-backend-test ./backend
docker run --rm securecommerce-backend-test
docker build --target test -t securecommerce-frontend-test ./frontend
docker run --rm securecommerce-frontend-test
```

Las imágenes de prueba contienen las herramientas de desarrollo; las imágenes de ejecución no las incluyen. CI también ejecuta SAST, análisis de dependencias, detección de secretos, Trivy y generación de SBOM.

## Backup cifrado

Defina `BACKUP_ENCRYPTION_KEY` con al menos 32 caracteres y active el perfil opcional:

```powershell
docker compose --profile backup up -d backup
```

La copia incluye PostgreSQL y reportes, usa AES-256-CBC/PBKDF2, hash SHA-256 y retención predeterminada de 35 días. Consulte el [runbook](docs/backup-restore.md) antes de restaurar.

Desarrollo local sin Docker:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".\backend[dev]"
python -m uvicorn app.main:app --app-dir backend --reload --port 8001
cd frontend
npm ci
npm run dev
```

El readiness responderá `503 degraded` sin PostgreSQL y Redis; liveness seguirá respondiendo para confirmar que el proceso funciona.

## Estructura

- `backend/`: FastAPI, Celery, configuración, Alembic y pruebas.
- `frontend/`: React, Vite, TypeScript, Tailwind y pruebas.
- `infrastructure/`: proxy inverso Nginx.
- `docs/`: arquitectura, seguridad y operación.

## Seed y credenciales de demostración

El seed crea `administrador@demo.local`, `analista@demo.local` y `consulta@demo.local` para Comercializadora Maya, S.A., además de siete activos claramente ficticios. Todos usan exclusivamente el valor local de `DEMO_PASSWORD`. **Nunca reutilice esa contraseña ni ejecute el seed en producción.**

Los access tokens vencen en 15 minutos. Los refresh tokens rotativos se envían como cookies HttpOnly y no se almacenan en el navegador mediante `localStorage`.

## Uso multiempresa

Cada organización dispone de activos, evaluaciones, riesgos, incidentes, auditoría y reportes separados mediante `organization_id`. Un usuario asociado con varias empresas selecciona la organización al iniciar sesión y puede cambiarla desde **Mis empresas**. La organización seleccionada se conserva al renovar la sesión.

El registro, disponible solo para administradores con sesión iniciada, crea una organización y su primera cuenta `org_admin`. La cuenta local `administrador@demo.local` también es superadministradora de demostración y puede consultar o suspender organizaciones desde **Administración de plataforma**. Una organización suspendida no admite nuevos accesos ni renovación de sesiones.

## Problemas frecuentes

- `docker no se reconoce`: instale/inicie Docker Desktop y abra una terminal nueva.
- Puerto `8080` ocupado: defina `APP_PORT=8081` en `.env`.
- API `degraded`: revise `docker compose ps` y `docker compose logs postgres redis api`.
- Cambios de dependencias no reflejados: ejecute `docker compose build --no-cache api frontend`.
- Rendimiento bajo en OneDrive: pause temporalmente la sincronización o mueva el clon a un directorio local de desarrollo.

Consulte [arquitectura](docs/architecture.md), [despliegue](docs/deployment.md), [pruebas](docs/testing.md) y [política de seguridad](SECURITY.md).
