# Arquitectura

El MVP usa un monolito modular: navegador → Nginx → React/FastAPI → PostgreSQL, con Redis y Celery para trabajo asíncrono. La API se versiona bajo `/api/v1`. PostgreSQL y Redis permanecen en una red interna de Compose.

La separación modular prepara aislamiento multiempresa, RBAC, motor determinístico de riesgos, adaptadores de IA y almacenamiento compatible con S3. AWS ECS/Fargate, RDS, S3, KMS, Secrets Manager, CloudFront y WAF son el destino de producción previsto. Kubernetes queda fuera del MVP.

## Aislamiento multiempresa

La aplicación usa una URL compartida y resuelve el contexto empresarial durante la autenticación. `Membership` relaciona usuarios, organizaciones y roles. El token de acceso contiene el identificador de organización y cada repositorio filtra sus consultas por ese valor. Las sesiones persistentes también conservan la organización seleccionada para evitar cambios de contexto durante la renovación.

Los usuarios con varias membresías reciben una selección explícita antes de acceder y pueden cambiar de organización desde la aplicación. Los superadministradores de plataforma se identifican mediante `User.is_superadmin`; esta capacidad no elimina el filtro empresarial de los módulos operativos.
