#!/usr/bin/env bash
# CloudPOS — preparar USB permanente para backups
#
# Conecta una USB (ej. 16 GB) al SERVIDOR y corre:
#   sudo ./scripts/setup-backup-usb.sh
#
# Esto:
#   - te ayuda a etiquetar la partición como CLOUDPOS_BK
#   - crea /mnt/cloudpos-backup
#   - agrega línea a /etc/fstab (montaje por LABEL)
#   - monta ahora
#   - instala cron diario a las 03:00
#
set -euo pipefail

LABEL="${BACKUP_USB_LABEL:-CLOUDPOS_BK}"
MOUNT="${BACKUP_USB_MOUNT:-/mnt/cloudpos-backup}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_SCRIPT="${SCRIPT_DIR}/backup-usb.sh"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Corre con sudo: sudo $0" >&2
  exit 1
fi

echo "=== CloudPOS · setup backup USB ==="
echo "Etiqueta esperada: ${LABEL}"
echo "Punto de montaje:  ${MOUNT}"
echo

echo "Dispositivos de bloque detectados:"
lsblk -o NAME,SIZE,TYPE,FSTYPE,LABEL,MOUNTPOINT
echo

if ! command -v lsblk >/dev/null; then
  echo "lsblk no disponible" >&2
  exit 1
fi

# Buscar por label existente
DEV="$(blkid -L "${LABEL}" 2>/dev/null || true)"

if [[ -z "${DEV}" ]]; then
  echo "No se encontró ninguna partición con etiqueta ${LABEL}."
  echo
  echo "Si la USB está en blanco, elige el dispositivo correcto (ej. /dev/sdb1) y formatea:"
  echo
  echo "  # CUIDADO: esto BORRA todo lo de esa partición"
  echo "  sudo mkfs.ext4 -L ${LABEL} /dev/sdX1"
  echo
  echo "  # Alternativa si quieres leerla también en Windows:"
  echo "  sudo apt-get install -y dosfstools"
  echo "  sudo mkfs.vfat -n ${LABEL} /dev/sdX1"
  echo
  echo "Luego vuelve a correr: sudo $0"
  exit 1
fi

echo "Encontrada: ${DEV} (LABEL=${LABEL})"

mkdir -p "${MOUNT}"

FSTYPE="$(blkid -o value -s TYPE "${DEV}" || true)"
if [[ -z "${FSTYPE}" ]]; then
  echo "No se pudo detectar el filesystem de ${DEV}" >&2
  exit 1
fi

FSTAB_LINE="LABEL=${LABEL}  ${MOUNT}  ${FSTYPE}  defaults,nofail,x-systemd.device-timeout=10  0  2"

if grep -q "LABEL=${LABEL}" /etc/fstab 2>/dev/null; then
  echo "fstab ya tiene una entrada para LABEL=${LABEL} — no se duplica."
else
  echo "Agregando a /etc/fstab:"
  echo "  ${FSTAB_LINE}"
  cp -a /etc/fstab "/etc/fstab.bak.$(date +%Y%m%d%H%M%S)"
  echo "${FSTAB_LINE}" >> /etc/fstab
fi

if mountpoint -q "${MOUNT}"; then
  echo "Ya estaba montada en ${MOUNT}"
else
  mount "${MOUNT}"
  echo "Montada en ${MOUNT}"
fi

mkdir -p "${MOUNT}/cloudpos"
chmod 755 "${MOUNT}/cloudpos"

# Cron para el usuario que suele operar el stack (dueño del directorio del script)
OWNER="$(stat -c '%U' "${SCRIPT_DIR}" 2>/dev/null || echo root)"
CRON_LINE="0 3 * * * ${BACKUP_SCRIPT} >> /var/log/cloudpos-backup.log 2>&1"

echo
echo "Para instalar cron diario (03:00) como ${OWNER}:"
echo "  sudo -u ${OWNER} crontab -l 2>/dev/null | grep -v backup-usb.sh | { cat; echo '${CRON_LINE}'; } | sudo -u ${OWNER} crontab -"
echo
echo "O pégalo manualmente con: sudo -u ${OWNER} crontab -e"
echo
echo "Prueba ahora (sin esperar al cron):"
echo "  sudo -u ${OWNER} ${BACKUP_SCRIPT}"
echo
echo "=== Setup USB listo ==="
