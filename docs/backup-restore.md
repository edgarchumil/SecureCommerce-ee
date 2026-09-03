# Backup y restauración

Objetivos: RPO 24 horas, RTO 8 horas y retención de 35 días. El perfil `backup` crea diariamente un paquete con `pg_dump` y reportes, lo cifra con AES-256-CBC/PBKDF2, genera SHA-256 y elimina copias antiguas.

## Operación local

Defina una clave aleatoria de al menos 32 caracteres en `.env`; no la guarde en Git. Inicie el servicio periódico:

```powershell
docker compose --profile backup up -d backup
docker compose logs backup
```

Copia única y listado:

```powershell
docker compose --profile backup run --rm -e BACKUP_RUN_ONCE=true backup
docker compose --profile backup run --rm --entrypoint sh backup -c "ls -lh /backups"
```

Verifique una copia antes de restaurarla:

```powershell
docker compose --profile backup run --rm --entrypoint /usr/local/bin/verify.sh `
  -e BACKUP_FILE=/backups/securecommerce-FECHA.tar.enc backup
```

La restauración sobrescribe la base objetivo y los reportes. Ejecútela primero en un proyecto Compose aislado; requiere confirmación explícita:

```powershell
docker compose --profile backup run --rm --entrypoint /usr/local/bin/restore.sh `
  -e CONFIRM_RESTORE=RESTORE -e BACKUP_FILE=/backups/securecommerce-FECHA.tar.enc backup
```

Después valide migración, conteos, autenticación, aislamiento tenant, hashes de reportes y suite automática. Registre duración, responsable, fecha y hallazgos.

## Producción AWS

Use RDS con backups automáticos, PITR y retención de 35 días; S3 versionado con Object Lock cuando aplique; KMS; copia entre cuenta/región; acceso mínimo; alarmas por fallos y pruebas trimestrales. La clave local no reemplaza KMS ni Secrets Manager.
