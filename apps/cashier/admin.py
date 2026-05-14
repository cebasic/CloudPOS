from django.contrib import admin
from .models import CashSession, CashCut


@admin.register(CashSession)
class CashSessionAdmin(admin.ModelAdmin):
    list_display = ["pk", "opened_by", "opened_at", "status", "initial_cash", "closed_at"]
    list_filter = ["status"]
    raw_id_fields = ["opened_by", "closed_by"]


@admin.register(CashCut)
class CashCutAdmin(admin.ModelAdmin):
    list_display = ["pk", "session", "cut_type", "cut_by", "created_at", "total_sales", "cash_difference"]
    list_filter = ["cut_type"]
    raw_id_fields = ["cut_by", "session"]
