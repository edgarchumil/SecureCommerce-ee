#!/bin/sh
set -eu

: "${POSTGRES_HOST:=postgres}"
: "${POSTGRES_DB:=securecommerce}"
: "${POSTGRES_USER:=securecommerce}"
: "${BACKUP_INTERVAL_SECONDS:=86400}"
: "${BACKUP_RETENTION_DAYS:=35}"
: "${BACKUP_ENCRYPTION_KEY:?BACKUP_ENCRYPTION_KEY es obligatoria}"

umask 077
mkdir -p /backups

create_backup() {
  timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
  workdir="$(mktemp -d /tmp/securecommerce-backup.XXXXXX)"
  trap 'rm -rf "$workdir"' EXIT INT TERM

  pg_dump --host "$POSTGRES_HOST" --username "$POSTGRES_USER" \
    --dbname "$POSTGRES_DB" --format=custom --file "$workdir/database.dump"
  tar -C /data/reports -czf "$workdir/reports.tar.gz" .
  printf '%s\n' "$timestamp" > "$workdir/created-at-utc.txt"
  tar -C "$workdir" -cf - database.dump reports.tar.gz created-at-utc.txt |
    openssl enc -aes-256-cbc -salt -pbkdf2 -pass env:BACKUP_ENCRYPTION_KEY \
      -out "/backups/securecommerce-$timestamp.tar.enc"
  sha256sum "/backups/securecommerce-$timestamp.tar.enc" \
    > "/backups/securecommerce-$timestamp.tar.enc.sha256"
  find /backups -type f -mtime "+$BACKUP_RETENTION_DAYS" -delete
  rm -rf "$workdir"
  trap - EXIT INT TERM
  echo "Backup cifrado completado: $timestamp"
}

while true; do
  create_backup
  [ "${BACKUP_RUN_ONCE:-false}" = "true" ] && exit 0
  sleep "$BACKUP_INTERVAL_SECONDS"
done
