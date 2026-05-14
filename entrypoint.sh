#!/bin/sh
set -e

echo "Aplicando migraciones..."
python manage.py migrate --noinput

echo "Cargando datos iniciales..."
python manage.py seed_data

echo "Recolectando archivos estáticos..."
python manage.py collectstatic --noinput --clear

echo "Iniciando servidor Daphne..."
exec daphne -b 0.0.0.0 -p 8000 config.asgi:application
