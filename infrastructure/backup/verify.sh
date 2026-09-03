#!/bin/sh
set -eu

: "${BACKUP_FILE:?BACKUP_FILE es obligatorio}"
: "${BACKUP_ENCRYPTION_KEY:?BACKUP_ENCRYPTION_KEY es obligatoria}"
[ -f "$BACKUP_FILE" ] || { echo "Backup inexistente" >&2; exit 2; }
sha256sum -c "$BACKUP_FILE.sha256"
workdir="$(mktemp -d /tmp/securecommerce-verify.XXXXXX)"
trap 'rm -rf "$workdir"' EXIT INT TERM
openssl enc -d -aes-256-cbc -pbkdf2 -pass env:BACKUP_ENCRYPTION_KEY \
  -in "$BACKUP_FILE" | tar -C "$workdir" -xf -
pg_restore --list "$workdir/database.dump" >/dev/null
tar -tzf "$workdir/reports.tar.gz" >/dev/null
echo "Backup íntegro, descifrable y estructuralmente válido"
