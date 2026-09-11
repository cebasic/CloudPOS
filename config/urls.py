from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.shortcuts import redirect


urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls")),
    path("tables/", include("apps.tables.urls")),
    path("menu/", include("apps.menu.urls")),
    path("orders/", include("apps.orders.urls")),
    path("kitchen/", include("apps.kitchen.urls")),
    path("reports/", include("apps.reports.urls")),
    path("caja/", include("apps.cashier.urls")),
    path("reservaciones/", include("apps.reservations.urls")),
    path("ticket/", include("apps.tickets.urls")),
    path("negocio/", include("apps.business.urls")),
    path("inventario/", include("apps.inventory.urls")),
    path("", lambda request: redirect("orders:dashboard")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
