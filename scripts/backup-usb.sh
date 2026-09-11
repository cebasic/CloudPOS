#!/usr/bin/env bash
# CloudPOS — backup a USB (y copia local de respaldo)
#
# Requisitos en el servidor (una sola vez):
#   1. USB siempre conectada, etiqueta: CLOUDPOS_BK
#   2. Montaje fijo en /mnt/cloudpos-backup  (ver scripts/setup-backup-usb.sh)
#   3. Cron diario, ej.:
#        0 3 * * * /opt/cloudpos/scripts/backup-usb.sh >> /var/log/cloudpos-backup.log 2>&1
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
USB_MOUNT="${BACKUP_USB_MOUNT:-/mnt/cloudpos-backup}"
LOCAL_DIR="${BACKUP_LOCAL_DIR:-/opt/backups/cloudpos}"
LOG_TAG="cloudpos-backup"

log() { echo "[$(date '+%F %T')] $*"; }

log "==> Inicio backup USB"

# Siempre guardar también en disco local del server
mkdir -p "${LOCAL_DIR}"
LOCAL_FILE="$("${SCRIPT_DIR}/backup-db.sh" "${LOCAL_DIR}")"
log "Local: ${LOCAL_FILE}"

if [[ ! -d "${USB_MOUNT}" ]]; then
  log "ERROR: no existe ${USB_MOUNT}. Corre setup-backup-usb.sh primero."
  exit 1
fi

if ! mountpoint -q "${USB_MOUNT}"; then
  log "ERROR: USB no montada en ${USB_MOUNT}. ¿Está conectada y con etiqueta CLOUDPOS_BK?"
  # Intento suave de montar (por si fstab existe pero no montó)
  if mount "${USB_MOUNT}" 2>/dev/null; then
    log "Montaje recuperado."
  else
    exit 1
  fi
fi

USB_DIR="${USB_MOUNT}/cloudpos"
mkdir -p "${USB_DIR}"
USB_FILE="$("${SCRIPT_DIR}/backup-db.sh" "${USB_DIR}")"
log "USB:   ${USB_FILE}"
log "==> Backup terminado OK"
logger -t "${LOG_TAG}" "backup OK local=${LOCAL_FILE} usb=${USB_FILE}" || true
