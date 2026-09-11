from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class StockItem(models.Model):
    class ItemType(models.TextChoices):
        INGREDIENT = "ingredient", "Insumo"
        SELLABLE_UNIT = "sellable_unit", "Producto unitario"

    class Unit(models.TextChoices):
        PZ = "pza", "Pieza"
        KG = "kg", "Kilogramo"
        G = "g", "Gramo"
        L = "L", "Litro"
        ML = "ml", "Mililitro"
        BOX = "caja", "Caja"
        OTHER = "otro", "Otro"

    name = models.CharField("Nombre", max_length=120)
    item_type = models.CharField(
        "Tipo", max_length=20, choices=ItemType.choices, default=ItemType.INGREDIENT,
    )
    unit = models.CharField("Unidad", max_length=10, choices=Unit.choices, default=Unit.PZ)
    qty_on_hand = models.DecimalField(
        "Existencia", max_digits=12, decimal_places=3, default=Decimal("0"),
    )
    par_level = models.DecimalField(
        "Mínimo (par)", max_digits=12, decimal_places=3, default=Decimal("0"),
        help_text="Nivel deseado en almacén. Si la existencia baja de esto, aparece en Para comprar.",
    )
    reorder_qty = models.DecimalField(
        "Cantidad de reorden", max_digits=12, decimal_places=3, default=Decimal("0"),
        help_text="Si es > 0, se usa como mínimo sugerido al comprar; si no, se sugiere par − existencia.",
    )
    # Bebidas / productos 1:1 con un platillo del menú
    menu_item = models.OneToOneField(
        "menu.MenuItem",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stock_item",
        verbose_name="Platillo vinculado (1:1)",
    )
    is_active = models.BooleanField("Activo", default=True)
    notes = models.CharField("Notas", max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Ítem de inventario"
        verbose_name_plural = "Ítems de inventario"

    def __str__(self):
        return f"{self.name} ({self.qty_on_hand} {self.unit})"

    @property
    def is_below_par(self):
        return self.par_level > 0 and self.qty_on_hand < self.par_level

    @property
    def suggested_buy_qty(self):
        """Cantidad sugerida para llegar al par (o reorder_qty si es mayor)."""
        if self.par_level <= 0:
            return Decimal("0")
        gap = self.par_level - self.qty_on_hand
        if gap <= 0:
            return Decimal("0")
        if self.reorder_qty and self.reorder_qty > gap:
            return self.reorder_qty
        return gap


class StockMovement(models.Model):
    class Reason(models.TextChoices):
        PURCHASE = "purchase", "Compra / entrada"
        SALE_DEDUCT = "sale_deduct", "Venta (descuento)"
        COUNT_ADJUST = "count_adjust", "Ajuste por conteo"
        WASTE = "waste", "Merma"
        MANUAL = "manual", "Ajuste manual"

    stock_item = models.ForeignKey(
        StockItem, on_delete=models.CASCADE, related_name="movements",
    )
    reason = models.CharField(max_length=20, choices=Reason.choices)
    quantity_delta = models.DecimalField(
        max_digits=12, decimal_places=3,
        help_text="Positivo = entrada; negativo = salida.",
    )
    qty_before = models.DecimalField(max_digits=12, decimal_places=3)
    qty_after = models.DecimalField(max_digits=12, decimal_places=3)
    note = models.CharField(max_length=240, blank=True)
    order = models.ForeignKey(
        "orders.Order", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="stock_movements",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="stock_movements",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Movimiento de inventario"
        verbose_name_plural = "Movimientos de inventario"

    def __str__(self):
        sign = "+" if self.quantity_delta >= 0 else ""
        return f"{self.stock_item.name} {sign}{self.quantity_delta} ({self.get_reason_display()})"


class RecipeLine(models.Model):
    """Cantidad de un StockItem consumida por 1 unidad de MenuItem."""

    menu_item = models.ForeignKey(
        "menu.MenuItem", on_delete=models.CASCADE, related_name="recipe_lines",
    )
    stock_item = models.ForeignKey(
        StockItem, on_delete=models.CASCADE, related_name="recipe_lines",
    )
    quantity = models.DecimalField(
        "Cantidad por platillo", max_digits=12, decimal_places=3,
    )

    class Meta:
        ordering = ["menu_item__name", "stock_item__name"]
        unique_together = [("menu_item", "stock_item")]
        verbose_name = "Línea de receta"
        verbose_name_plural = "Líneas de receta"

    def __str__(self):
        return f"{self.menu_item.name}: {self.quantity} {self.stock_item.unit} {self.stock_item.name}"

    def clean(self):
        if self.quantity is not None and self.quantity <= 0:
            raise ValidationError({"quantity": "La cantidad debe ser mayor a 0."})


class StockCount(models.Model):
    """Sesión de conteo físico que genera ajustes count_adjust."""

    counted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="stock_counts",
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Conteo de inventario"
        verbose_name_plural = "Conteos de inventario"

    def __str__(self):
        return f"Conteo #{self.pk} — {self.created_at:%d/%m/%Y %H:%M}"


class StockCountLine(models.Model):
    count = models.ForeignKey(StockCount, on_delete=models.CASCADE, related_name="lines")
    stock_item = models.ForeignKey(StockItem, on_delete=models.CASCADE, related_name="count_lines")
    qty_system = models.DecimalField(max_digits=12, decimal_places=3)
    qty_counted = models.DecimalField(max_digits=12, decimal_places=3)
    difference = models.DecimalField(max_digits=12, decimal_places=3, default=Decimal("0"))

    class Meta:
        unique_together = [("count", "stock_item")]
        verbose_name = "Línea de conteo"
        verbose_name_plural = "Líneas de conteo"
