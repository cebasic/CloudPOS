from django.contrib import admin

from .models import TicketSettings


@admin.register(TicketSettings)
class TicketSettingsAdmin(admin.ModelAdmin):
    list_display = ("business_name", "phone", "updated_at")

    def has_add_permission(self, request):
        # Singleton: no permitir crear filas adicionales.
        return not TicketSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
