# CocosBarrancos - Sistema de Gestion de Restaurante

Aplicacion web monolitica para la gestion de un restaurante, construida con Django.

## Stack Tecnologico

- **Backend:** Django 5.1, Django Channels (WebSockets)
- **Base de datos:** PostgreSQL
- **Canal en tiempo real:** Redis + Django Channels
- **Frontend:** Tailwind CSS (CDN) + HTMX + Alpine.js

## Requisitos

- Python 3.11+
- PostgreSQL
- Redis

## Instalacion

```bash
# 1. Crear y activar entorno virtual
python3 -m venv venv
source venv/bin/activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Crear base de datos en PostgreSQL
createdb restaurant_db
# O si prefieres usar psql:
# psql -c "CREATE DATABASE restaurant_db;"

# 4. Configurar variables de entorno (opcional, usa defaults para desarrollo)
export DB_NAME=restaurant_db
export DB_USER=postgres
export DB_PASSWORD=postgres
export DB_HOST=127.0.0.1

# 5. Ejecutar migraciones
python manage.py migrate

# 6. Cargar datos de ejemplo
python manage.py seed_data

# 7. Iniciar el servidor
python manage.py runserver
# O con Daphne para WebSocket:
daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

## Usuarios de prueba

| Usuario  | Contrasena  | Rol            |
|----------|-------------|----------------|
| admin    | admin123    | Administrador  |
| gerente  | gerente123  | Gerente        |
| mesero1  | mesero123   | Mesero         |
| mesero2  | mesero123   | Mesero         |
| cocina   | cocina123   | Cocina         |

## Modulos

- **Login/Auth:** Autenticacion, usuarios, roles y permisos
- **Mesas:** Alta y gestion de mesas con estado visual
- **Menu:** Categorias y platillos con toggle de disponibilidad
- **Ordenes:** Crear, editar, agregar items, cambiar estados
- **Cocina:** Pantalla en tiempo real via WebSocket (tablero Kanban)
- **Reportes:** Ventas, platillos populares, ordenes por mesero, graficas

## Notas

- El servidor de desarrollo (`runserver`) no soporta WebSockets. Usa `daphne` para la funcionalidad de cocina en tiempo real.
- Redis debe estar corriendo en `localhost:6379` para el channel layer.
