from django.contrib import admin
from .models import Category, MenuItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "order"]
    ordering = ["order"]


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "price", "available", "requires_kitchen"]
    list_filter = ["category", "available", "requires_kitchen"]
    list_editable = ["available", "requires_kitchen"]
