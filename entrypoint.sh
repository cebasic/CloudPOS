#!/bin/sh
set -e

echo "Aplicando migraciones..."
python manage.py migrate --noinput

# seed_data solo carga demos en BD vacía; en reinicios/producción se salta solo.
# Forzar omisión: SEED_DATA=false | Forzar intento: SEED_DATA=true (sigue sin --force)
if [ "${SEED_DATA:-true}" = "false" ]; then
  echo "SEED_DATA=false — omitiendo datos iniciales"
else
  echo "Cargando datos iniciales (solo si la BD está vacía)..."
  python manage.py seed_data
fi

echo "Recolectando archivos estáticos..."
python manage.py collectstatic --noinput --clear

echo "Iniciando servidor Daphne..."
exec daphne -b 0.0.0.0 -p 8000 config.asgi:application
