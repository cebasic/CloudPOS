from django.contrib import admin

from .models import RecipeLine, StockCount, StockCountLine, StockItem, StockMovement


class RecipeLineInline(admin.TabularInline):
    model = RecipeLine
    extra = 1


@admin.register(StockItem)
class StockItemAdmin(admin.ModelAdmin):
    list_display = ["name", "item_type", "unit", "qty_on_hand", "par_level", "is_active"]
    list_filter = ["item_type", "is_active", "unit"]
    search_fields = ["name"]


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ["created_at", "stock_item", "reason", "quantity_delta", "qty_after", "created_by"]
    list_filter = ["reason"]


@admin.register(RecipeLine)
class RecipeLineAdmin(admin.ModelAdmin):
    list_display = ["menu_item", "stock_item", "quantity"]


class StockCountLineInline(admin.TabularInline):
    model = StockCountLine
    extra = 0
    readonly_fields = ["stock_item", "qty_system", "qty_counted", "difference"]


@admin.register(StockCount)
class StockCountAdmin(admin.ModelAdmin):
    list_display = ["id", "created_at", "counted_by"]
    inlines = [StockCountLineInline]
