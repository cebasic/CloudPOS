#!/usr/bin/env bash
# CloudPOS — actualizar el POS en el servidor por SSH
#
# Uso (en el server):
#   cd /opt/cloudpos
#   ./scripts/update.sh
#
# Opcional:
#   UPDATE_BRANCH=main ./scripts/update.sh
#   SKIP_BACKUP=1 ./scripts/update.sh          # no recomendado
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${ROOT_DIR}"

BRANCH="${UPDATE_BRANCH:-main}"
LOCAL_DIR="${BACKUP_LOCAL_DIR:-/opt/backups/cloudpos}"
USB_MOUNT="${BACKUP_USB_MOUNT:-/mnt/cloudpos-backup}"

log() { echo "[$(date '+%F %T')] $*"; }
die() { log "ERROR: $*"; exit 1; }

log "==> CloudPOS update (branch=${BRANCH})"
log "    root=${ROOT_DIR}"

# --- 1) Backup previo ---
if [[ "${SKIP_BACKUP:-0}" != "1" ]]; then
  log "==> Backup pre-update"
  mkdir -p "${LOCAL_DIR}"
  LOCAL_FILE="$("${SCRIPT_DIR}/backup-db.sh" "${LOCAL_DIR}")"
  log "    local: ${LOCAL_FILE}"

  if mountpoint -q "${USB_MOUNT}" 2>/dev/null; then
    USB_DIR="${USB_MOUNT}/cloudpos"
    mkdir -p "${USB_DIR}"
    USB_FILE="$("${SCRIPT_DIR}/backup-db.sh" "${USB_DIR}")"
    log "    usb:   ${USB_FILE}"
  else
    log "    (USB no montada — solo backup local; no es bloqueante)"
  fi
else
  log "==> SKIP_BACKUP=1 — sin backup"
fi

# --- 2) Código ---
log "==> git fetch / pull (${BRANCH})"
if [[ ! -d .git ]]; then
  die "no hay repositorio git en ${ROOT_DIR}"
fi

git fetch origin "${BRANCH}"
# Evitar pisar cambios locales accidentales
if [[ -n "$(git status --porcelain)" ]]; then
  die "hay cambios locales sin commit en el server. Revísalos antes de actualizar."
fi

CURRENT="$(git rev-parse --abbrev-ref HEAD)"
if [[ "${CURRENT}" != "${BRANCH}" ]]; then
  log "    checkout ${BRANCH} (estaba en ${CURRENT})"
  git checkout "${BRANCH}"
fi

BEFORE="$(git rev-parse --short HEAD)"
git pull --ff-only origin "${BRANCH}"
AFTER="$(git rev-parse --short HEAD)"
log "    ${BEFORE} → ${AFTER}"

# No usar override de desarrollo en producción
if [[ -f docker-compose.override.yml ]]; then
  log "    aviso: docker-compose.override.yml presente — renombrando a .dev para no montar código en vivo"
  mv -f docker-compose.override.yml docker-compose.override.yml.dev
fi

# --- 3) Rebuild / restart ---
log "==> docker compose up -d --build"
docker compose up -d --build

# --- 4) Health check ---
log "==> esperando a que responda HTTP..."
OK=0
for i in $(seq 1 30); do
  if curl -fsS -o /dev/null -w "%{http_code}" http://127.0.0.1/accounts/login/ 2>/dev/null | grep -Eq '200|301|302'; then
    OK=1
    break
  fi
  sleep 2
done

log "==> estado contenedores"
docker compose ps

if [[ "${OK}" -ne 1 ]]; then
  die "el POS no respondió a tiempo en http://127.0.0.1/ — revisa: docker compose logs --tail=80 web"
fi

log "==> Update OK. POS respondiendo."
log "    Prueba desde la caja: http://$(hostname -I 2>/dev/null | awk '{print $1}')"
