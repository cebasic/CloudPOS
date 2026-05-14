from django.contrib import admin
from .models import Reservation


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ["customer_name", "date", "time", "party_size", "table", "status", "created_by"]
    list_filter = ["status", "date"]
    search_fields = ["customer_name", "customer_phone"]
