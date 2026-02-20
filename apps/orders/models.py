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

    table = models.ForeignKey("tables.Table", on_delete=models.CASCADE, related_name="orders", verbose_name="Mesa")
    waiter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders", verbose_name="Mesero")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Orden"
        verbose_name_plural = "Ordenes"

    def __str__(self):
        return f"Orden #{self.pk} - Mesa {self.table.number}"

    @property
    def total(self):
        return sum(item.subtotal for item in self.items.all())

    def sync_status(self):
        """Auto-update order status based on item statuses."""
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

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="payment")
    method = models.CharField(max_length=10, choices=Method.choices)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    amount_received = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Solo para pagos en efectivo",
    )
    change_due = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Cambio a devolver",
    )
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
