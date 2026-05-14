from django.conf import settings
from django.db import models


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendiente"
        IN_PROGRESS = "in_progress", "En preparacion"
        READY = "ready", "Lista"
        DELIVERED = "delivered", "Entregada"
        CLOSED = "closed", "Cerrada"
        CANCELLED = "cancelled", "Cancelada"

    class DiscountType(models.TextChoices):
        NONE = "none", "Sin descuento"
        PERCENTAGE = "percentage", "Porcentaje"
        FIXED = "fixed", "Monto fijo"

    table = models.ForeignKey("tables.Table", on_delete=models.CASCADE, related_name="orders", verbose_name="Mesa")
    waiter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders", verbose_name="Mesero")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Discount
    discount_type = models.CharField(max_length=15, choices=DiscountType.choices, default=DiscountType.NONE)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_reason = models.CharField(max_length=200, blank=True)
    discount_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="discounts_applied",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Orden"
        verbose_name_plural = "Ordenes"

    def __str__(self):
        return f"Orden #{self.pk} - Mesa {self.table.number}"

    @property
    def subtotal(self):
        return sum(item.subtotal for item in self.items.all())

    @property
    def total(self):
        return self.subtotal

    @property
    def discount_amount(self):
        if self.discount_type == "percentage":
            return round(self.subtotal * self.discount_value / 100, 2)
        if self.discount_type == "fixed":
            return min(self.discount_value, self.subtotal)
        return 0

    @property
    def final_total(self):
        return self.subtotal - self.discount_amount

    def sync_status(self):
        if self.status in (self.Status.CLOSED, self.Status.CANCELLED):
            return
        items = list(self.items.all())
        if not items:
            return
        statuses = {item.status for item in items}
        if statuses == {"delivered"}:
            self.status = self.Status.DELIVERED
        elif statuses == {"ready"}:
            self.status = self.Status.READY
        elif "ready" in statuses and statuses <= {"ready", "delivered"}:
            self.status = self.Status.READY
        elif statuses != {"pending"}:
            self.status = self.Status.IN_PROGRESS
        self.save(update_fields=["status", "updated_at"])


class OrderItem(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendiente"
        PREPARING = "preparing", "Preparando"
        READY = "ready", "Listo"
        DELIVERED = "delivered", "Entregado"

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    menu_item = models.ForeignKey("menu.MenuItem", on_delete=models.CASCADE, related_name="order_items")
    quantity = models.PositiveIntegerField(default=1)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        verbose_name = "Item de Orden"
        verbose_name_plural = "Items de Orden"

    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name}"

    @property
    def subtotal(self):
        return self.menu_item.price * self.quantity


class Payment(models.Model):
    class Method(models.TextChoices):
        CASH = "cash", "Efectivo"
        CARD = "card", "Tarjeta"
        MIXED = "mixed", "Mixto"

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="payment")
    method = models.CharField(max_length=10, choices=Method.choices)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    tip = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Cash payment fields
    amount_received = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Solo para pagos en efectivo",
    )
    change_due = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Cambio a devolver",
    )

    # Mixed payment fields
    cash_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    card_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    collected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payments",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"

    def __str__(self):
        return f"Pago {self.get_method_display()} - Orden #{self.order_id} - ${self.total}"

    @property
    def grand_total(self):
        return self.total + self.tip
