# CocosBarrancos — Sistema de Gestión de Restaurante

Aplicación web monolítica para la gestión de un restaurante, construida con Django.

## Stack Tecnológico

- **Backend:** Django 5.1, Django Channels (WebSockets), Daphne (ASGI)
- **Base de datos:** PostgreSQL
- **Canal en tiempo real:** Valkey/Redis + Django Channels
- **Frontend:** Tailwind CSS (CDN Play), HTMX, Alpine.js
- **Tema:** Dark UI consistente con paleta slate + brand naranja

## Requisitos

- Python 3.11+
- PostgreSQL
- Valkey o Redis

## Levantar con Docker (recomendado)

La forma más sencilla de correr el proyecto en cualquier máquina sin instalar dependencias.

**Requisito:** tener [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado.

```bash
# Primera vez (construye la imagen e inicia todo)
docker compose up --build

# Arranques posteriores
docker compose up

# En background
docker compose up -d

# Detener
docker compose down
```

Al arrancar, el contenedor web ejecuta migraciones, intenta `seed_data` **solo si la base está vacía** (no vuelve a crear demos en cada reinicio) y recoge estáticos. La app queda disponible en **http://localhost**.

> En producción ya configurada puedes poner `SEED_DATA=false` en `.env`. Para forzar demos otra vez: `docker compose exec web python manage.py seed_data --force`.

> Para personalizar la configuración (base de datos, secret key, etc.) edita el archivo `.env` antes de levantar los contenedores. Usa `.env.example` como referencia.

## Operación en servidor (backup / update)

Scripts en `scripts/` (pensados para el PC servidor en `/opt/cloudpos`):

```bash
# Actualizar el POS por SSH (backup + git pull + rebuild)
./scripts/update.sh

# Preparar USB permanente de backups (una vez, con sudo)
sudo ./scripts/setup-backup-usb.sh

# Backup manual a USB + disco local
./scripts/backup-usb.sh
```

La USB debe quedar **siempre conectada** al servidor, con etiqueta `CLOUDPOS_BK`, montada en `/mnt/cloudpos-backup`.

## Instalación manual

```bash
# 1. Crear y activar entorno virtual
python3 -m venv venv
source venv/bin/activate        # bash/zsh
source venv/bin/activate.fish   # fish

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Crear base de datos en PostgreSQL
createdb restaurant_db

# 4. Configurar variables de entorno (opcional, usa defaults para desarrollo)
export DB_NAME=restaurant_db
export DB_USER=postgres
export DB_PASSWORD=postgres
export DB_HOST=127.0.0.1

# 5. Ejecutar migraciones
python manage.py migrate

# 6. Cargar datos de ejemplo
python manage.py seed_data

# 7. Iniciar Valkey (Redis)
sudo systemctl start valkey

# 8. Iniciar el servidor con Daphne (requerido para WebSockets)
daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

> El servidor de desarrollo (`runserver`) no soporta WebSockets. Usa `daphne` para la funcionalidad de cocina y notificaciones en tiempo real.

## Usuarios de prueba

| Usuario  | Contraseña  | Rol            |
|----------|-------------|----------------|
| admin    | admin123    | Administrador  |
| gerente  | gerente123  | Gerente        |
| mesero1  | mesero123   | Mesero         |
| mesero2  | mesero123   | Mesero         |
| cocina   | cocina123   | Cocina         |
| cajero   | cajero123   | Cajero         |

## Módulos

### Autenticación y Roles
Control de acceso basado en roles. Cada rol tiene acceso a vistas específicas y es redirigido a su pantalla principal al iniciar sesión.

| Rol           | Acceso principal |
|---------------|-----------------|
| Administrador | Todo el sistema |
| Gerente       | Todo excepto administración de usuarios |
| Mesero        | Órdenes, reservaciones |
| Cocina        | Pantalla de cocina, 86 Rápido |
| Cajero        | Caja, órdenes (cobro), reservaciones |

### Mesas
Alta y gestión de mesas con estado visual (disponible / ocupada / reservada). El estado se actualiza automáticamente al crear o cerrar órdenes.

### Menú
Categorías y platillos con precios e imágenes. Toggle de disponibilidad individual desde el panel de administración.

### 86 Rápido
Pantalla accesible a cocina, gerentes y administradores para marcar platillos como no disponibles (86'd) en tiempo real mediante HTMX, sin recargar la página. Los cambios aplican inmediatamente en nuevas órdenes.

### Órdenes
- Crear orden asignando mesa (solo si la caja está abierta)
- Agregar / eliminar ítems con notas por ítem
- Cambiar estado: Pendiente → En progreso → Listo → Entregado → Cerrado
- **Descuentos y cortesías:** aplicar descuento porcentual o monto fijo con motivo (acceso: admin / gerente / cajero)
- **Cobro con tip:** selector rápido de propina (10 / 15 / 20 % o monto libre)
- **Pago mixto:** dividir el cobro entre efectivo y tarjeta
- Recibo final con desglose de subtotal, descuento, total y propina

### Cocina
Tablero Kanban en tiempo real vía WebSocket. El personal de cocina actualiza el estado de cada ítem; cuando un ítem queda listo, se envía una notificación automática al mesero correspondiente.

### Caja (Cajero)
- **Apertura de sesión:** registra el fondo inicial del día
- **Corte parcial:** arqueo en cualquier momento sin cerrar la sesión; muestra diferencia entre lo contado y lo esperado en caja (verde / amarillo / rojo)
- **Corte final:** cierra la sesión del día con snapshot de ventas en efectivo, tarjeta, propinas y gastos
- **Gastos del día:** registro de gastos operativos (insumos, servicios, personal, otros) asociados a la sesión activa
- **Gate de órdenes:** si no hay caja abierta, no se pueden crear órdenes nuevas (banner de advertencia en el dashboard)
- Historial de sesiones y cortes con detalle de diferencias

### Reservaciones
- Crear y editar reservaciones con datos del cliente (nombre, teléfono, fecha, hora, número de personas, mesa asignada y notas)
- Vista por fecha con navegador de día
- Panel de próximas reservaciones (pendientes y confirmadas)
- Cambio rápido de estado: Pendiente → Confirmada → Sentada → Cancelada / No se presentó

### Reportes
Filtrable por rango de fechas. Incluye:
- **KPIs:** total de órdenes, ingresos, ticket promedio, propinas totales, descuentos aplicados, tasa de cancelación
- **Desglose de pago:** efectivo vs tarjeta vs mixto
- **Gráfica diaria:** barras de ingresos + línea de conteo de órdenes (doble eje)
- **Gráfica horaria:** distribución de órdenes por hora (para vista de un solo día)
- **Platillos más vendidos:** top 10 con barra de progreso relativa
- **Órdenes por mesero**
- **Exportar CSV:** incluye descuento y propina por orden

## Estructura de la Aplicación

```
apps/
├── accounts/     # Usuarios, roles, autenticación
├── cashier/      # Caja, sesiones, cortes, gastos
├── kitchen/      # Pantalla de cocina (WebSocket)
├── menu/         # Categorías, platillos, 86 rápido
├── orders/       # Órdenes, pagos, descuentos
├── reports/      # Reportes y exportación CSV
├── reservations/ # Reservaciones de mesas
└── tables/       # Gestión de mesas
```

## Notas de Desarrollo

- Valkey (compatible con Redis) debe estar corriendo en `localhost:6379` para el channel layer de WebSockets.
- En fish shell activar el venv con `source venv/bin/activate.fish`.
- Las clases de Tailwind aplicadas dinámicamente con Alpine.js deben usar `:style` con valores CSS directos (el Play CDN no genera CSS para clases custom aplicadas post-render).
- Los componentes Alpine.js se registran con `Alpine.data()` dentro del evento `alpine:init` para garantizar que estén disponibles antes de que Alpine inicialice el DOM.
