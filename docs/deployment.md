# Despliegue

Docker Compose es el entorno local. Nginx expone el puerto configurable `APP_PORT` y los almacenes no tienen puertos públicos. Producción se orientará a ECS/Fargate, RDS PostgreSQL, ElastiCache/Redis, S3, KMS, Secrets Manager, CloudFront y WAF, con TLS y HSTS en el borde.

No use los valores predeterminados de desarrollo en producción. La infraestructura AWS como código se añadirá después de validar el MVP.

La URL recomendada de producción es `https://app.securecommerceadvisor.com`, con `/registro` para altas de MIPYMES y `/login` para usuarios existentes. El modelo actual no requiere subdominios por cliente; el contexto se selecciona después de autenticar y se valida en la API.
