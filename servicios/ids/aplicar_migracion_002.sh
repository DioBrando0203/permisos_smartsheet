#!/usr/bin/env bash
set -euo pipefail

# Ejecutar desde cualquier carpeta como usuario con sudo; no toca Smartsheet.
base_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
backup_dir="$HOME/galp_backups"
umask 077
mkdir -p "$backup_dir"
backup_file=$(mktemp "$backup_dir/galp_servicios_XXXXXXXX.dump")

sudo -u postgres pg_dump -Fc -d galp_servicios > "$backup_file"
pg_restore --list "$backup_file" > /dev/null
printf 'Respaldo creado y legible: %s\n' "$backup_file"
sudo -u postgres psql -X -v ON_ERROR_STOP=1 -d galp_servicios \
  < "$base_dir/sql/002_auditoria_inicializacion.sql"
sudo -u postgres psql -X -v ON_ERROR_STOP=1 -d galp_servicios -c '\dt'
