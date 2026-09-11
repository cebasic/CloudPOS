#!/usr/bin/env bash
# CloudPOS — dump de PostgreSQL (uso interno / llamado por otros scripts)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${ROOT_DIR}"

if [[ -f "${ROOT_DIR}/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "${ROOT_DIR}/.env"
  set +a
fi

DB_NAME="${DB_NAME:-restaurant_db}"
DB_USER="${DB_USER:-postgres}"
KEEP_DAYS="${BACKUP_KEEP_DAYS:-14}"
STAMP="$(date +%Y-%m-%d_%H%M%S)"
FILENAME="cloudpos_${STAMP}.sql.gz"

DEST_DIR="${1:-}"
if [[ -z "${DEST_DIR}" ]]; then
  echo "Uso: $0 <directorio_destino>" >&2
  exit 1
fi

mkdir -p "${DEST_DIR}"
OUT="${DEST_DIR}/${FILENAME}"

echo "==> Backup → ${OUT}"

if ! docker compose ps --status running --services 2>/dev/null | grep -qx db; then
  echo "ERROR: el contenedor 'db' no está corriendo. ¿Levantaste docker compose?" >&2
  exit 1
fi

docker compose exec -T db \
  pg_dump -U "${DB_USER}" --no-owner --no-acl "${DB_NAME}" \
  | gzip -c > "${OUT}"

# Evitar dejar un gzip vacío si pg_dump falló a medias
if [[ ! -s "${OUT}" ]]; then
  rm -f "${OUT}"
  echo "ERROR: el backup quedó vacío." >&2
  exit 1
fi

SIZE="$(du -h "${OUT}" | awk '{print $1}')"
echo "    OK (${SIZE})"

# Rotación: borrar dumps más viejos que KEEP_DAYS
find "${DEST_DIR}" -maxdepth 1 -type f -name 'cloudpos_*.sql.gz' -mtime "+${KEEP_DAYS}" -print -delete \
  | sed 's/^/    rotado: /' || true

echo "${OUT}"
