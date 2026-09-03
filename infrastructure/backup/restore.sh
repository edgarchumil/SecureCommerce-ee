#!/bin/sh
set -eu

: "${BACKUP_FILE:?BACKUP_FILE es obligatorio}"
: "${BACKUP_ENCRYPTION_KEY:?BACKUP_ENCRYPTION_KEY es obligatoria}"
: "${CONFIRM_RESTORE:?Defina CONFIRM_RESTORE=RESTORE para autorizar}"
[ "$CONFIRM_RESTORE" = "RESTORE" ] || { echo "Confirmación inválida" >&2; exit 2; }
[ -f "$BACKUP_FILE" ] || { echo "Backup inexistente" >&2; exit 2; }
sha256sum -c "$BACKUP_FILE.sha256"

workdir="$(mktemp -d /tmp/securecommerce-restore.XXXXXX)"
trap 'rm -rf "$workdir"' EXIT INT TERM
openssl enc -d -aes-256-cbc -pbkdf2 -pass env:BACKUP_ENCRYPTION_KEY \
  -in "$BACKUP_FILE" | tar -C "$workdir" -xf -
pg_restore --clean --if-exists --no-owner --no-privileges \
  --host "${POSTGRES_HOST:-postgres}" --username "${POSTGRES_USER:-securecommerce}" \
  --dbname "${POSTGRES_DB:-securecommerce}" "$workdir/database.dump"
rm -rf /data/reports/*
tar -C /data/reports -xzf "$workdir/reports.tar.gz"
echo "Restauración completada y hash verificado"
