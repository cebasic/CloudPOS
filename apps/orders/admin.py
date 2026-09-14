from django.contrib import admin
from .models import Order, OrderItem, Payment


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


class PaymentInline(admin.StackedInline):
    model = Payment
    extra = 0
    max_num = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "order_type", "table", "customer_name", "waiter", "status", "created_at"]
    list_filter = ["order_type", "status", "created_at"]
    search_fields = ["customer_name", "customer_phone", "id"]
    inlines = [OrderItemInline, PaymentInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["id", "order", "method", "total", "amount_received", "change_due", "collected_by", "created_at"]
    list_filter = ["method", "created_at"]
