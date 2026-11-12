#!/usr/bin/env bash
set -euo pipefail

# Crea la tabla obs_comentario (SPEC-B17). Ejecutar como usuario con sudo; no toca Smartsheet
# ni las tablas de IDs. Respalda antes y comprueba que los conteos de IDs no cambien.
base_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
backup_dir="$HOME/galp_backups"
umask 077
mkdir -p "$backup_dir"
backup_file=$(mktemp "$backup_dir/galp_antes_004_XXXXXXXX.dump")
psql_admin=(sudo -u postgres psql -X -v ON_ERROR_STOP=1 -d galp_servicios)
counts="SELECT (SELECT count(*) FROM asignacion_id), (SELECT count(*) FROM secuencia_id), (SELECT count(*) FROM auditoria_id)"

sudo -u postgres pg_dump -Fc -d galp_servicios > "$backup_file"
pg_restore --list "$backup_file" > /dev/null
printf 'Respaldo creado y legible: %s\n' "$backup_file"
before=$("${psql_admin[@]}" -At -c "$counts")
"${psql_admin[@]}" < "$base_dir/sql/004_obs_comentario.sql"
after=$("${psql_admin[@]}" -At -c "$counts")
if [[ "$before" != "$after" ]]; then
  printf 'Los conteos de IDs cambiaron (%s -> %s); revisar.\n' "$before" "$after" >&2
  exit 1
fi
"${psql_admin[@]}" -c '\dt obs_comentario'
printf 'Migración 004 aplicada; IDs sin cambios (%s).\n' "$after"
