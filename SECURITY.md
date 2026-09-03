# Política de seguridad

No publique vulnerabilidades en incidencias públicas. Use el canal privado definido por el responsable del repositorio; mientras no exista uno, contacte directamente al propietario.

## Controles implementados

- Secretos mediante variables de entorno; PostgreSQL y Redis en red interna.
- API y worker sin privilegios; CORS restrictivo, cabeceras defensivas y rate limit.
- Argon2id, JWT breve, refresh rotativo/revocable, MFA TOTP, bloqueo temporal y RBAC.
- Aislamiento multiempresa y auditoría con identificador de correlación validado.
- Bandit, pip-audit, npm audit, Gitleaks, Trivy, Dependabot y SBOM SPDX en CI.
- Reportes con autorización por organización y hash SHA-256.
- Backups locales cifrados con AES-256-CBC/PBKDF2 y hash de integridad.

## Reporte de vulnerabilidades

Incluya versión, impacto, pasos mínimos de reproducción y mitigaciones conocidas. No adjunte datos reales, tokens ni evidencias empresariales. El responsable debe acusar recibo en 3 días hábiles y priorizar según impacto y explotabilidad.

## Riesgos aceptados para el MVP

- OAuth2/OIDC externo, WebAuthn y RLS de PostgreSQL no están activados.
- TLS, HSTS, WAF, KMS y Secrets Manager corresponden al borde AWS de producción.
- El almacenamiento local debe sustituirse en producción por S3 con KMS y enlaces firmados.
- La entrega de invitaciones y recuperación requiere un proveedor transaccional.

Nunca registre contraseñas, tokens, llaves, secretos, códigos MFA o evidencias sensibles completas.
