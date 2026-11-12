#!/usr/bin/env bash
set -euo pipefail

# Crea id_retirado y permite retirar IDs al cambiar el cliente (SPEC-ID01 ID-44).
# Ejecutar como usuario con sudo; no toca Smartsheet
# ni los datos de IDs. Respalda antes y comprueba que los conteos de IDs no cambien.
base_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
backup_dir="$HOME/galp_backups"
umask 077
mkdir -p "$backup_dir"
backup_file=$(mktemp "$backup_dir/galp_antes_005_XXXXXXXX.dump")
psql_admin=(sudo -u postgres psql -X -v ON_ERROR_STOP=1 -d galp_servicios)
counts="SELECT (SELECT count(*) FROM asignacion_id), (SELECT count(*) FROM secuencia_id), (SELECT count(*) FROM auditoria_id)"

sudo -u postgres pg_dump -Fc -d galp_servicios > "$backup_file"
pg_restore --list "$backup_file" > /dev/null
printf 'Respaldo creado y legible: %s\n' "$backup_file"
before=$("${psql_admin[@]}" -At -c "$counts")
"${psql_admin[@]}" < "$base_dir/sql/005_cambio_cliente.sql"
after=$("${psql_admin[@]}" -At -c "$counts")
if [[ "$before" != "$after" ]]; then
  printf 'Los conteos de IDs cambiaron (%s -> %s); revisar.\n' "$before" "$after" >&2
  exit 1
fi
"${psql_admin[@]}" -c '\dt id_retirado'
printf 'Migración 005 aplicada; IDs sin cambios (%s).\n' "$after"
