"""Servicios de inventario: kardex, descuento por venta, sugerencias de compra."""
from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import F, Q, Sum
from django.utils import timezone

from .models import RecipeLine, StockItem, StockMovement


def apply_movement(
    *,
    stock_item: StockItem,
    reason: str,
    quantity_delta: Decimal,
    user=None,
    note: str = "",
    order=None,
) -> StockMovement:
    """Aplica un movimiento al kardex y actualiza qty_on_hand. Permite negativo."""
    quantity_delta = Decimal(quantity_delta)
    if quantity_delta == 0:
        raise ValueError("quantity_delta no puede ser 0")

    with transaction.atomic():
        item = StockItem.objects.select_for_update().get(pk=stock_item.pk)
        qty_before = item.qty_on_hand
        qty_after = qty_before + quantity_delta
        item.qty_on_hand = qty_after
        item.save(update_fields=["qty_on_hand", "updated_at"])
        movement = StockMovement.objects.create(
            stock_item=item,
            reason=reason,
            quantity_delta=quantity_delta,
            qty_before=qty_before,
            qty_after=qty_after,
            note=note,
            order=order,
            created_by=user if getattr(user, "is_authenticated", False) else None,
        )
    return movement


def register_purchase(*, stock_item: StockItem, quantity: Decimal, user=None, note: str = "") -> StockMovement:
    quantity = Decimal(quantity)
    if quantity <= 0:
        raise ValueError("La cantidad de compra debe ser positiva")
    return apply_movement(
        stock_item=stock_item,
        reason=StockMovement.Reason.PURCHASE,
        quantity_delta=quantity,
        user=user,
        note=note or "Entrada por compra",
    )


def register_manual_adjust(*, stock_item: StockItem, quantity_delta: Decimal, user=None, note: str = "") -> StockMovement:
    return apply_movement(
        stock_item=stock_item,
        reason=StockMovement.Reason.MANUAL,
        quantity_delta=Decimal(quantity_delta),
        user=user,
        note=note or "Ajuste manual",
    )


def register_waste(*, stock_item: StockItem, quantity: Decimal, user=None, note: str = "") -> StockMovement:
    quantity = Decimal(quantity)
    if quantity <= 0:
        raise ValueError("La merma debe ser positiva")
    return apply_movement(
        stock_item=stock_item,
        reason=StockMovement.Reason.WASTE,
        quantity_delta=-quantity,
        user=user,
        note=note or "Merma",
    )


def deduct_for_order(order, user=None) -> list[StockMovement]:
    """
    Descuenta inventario al cobrar una orden.
    - Receta del platillo × cantidad
    - O vínculo 1:1 sellable_unit ↔ MenuItem (−1 por unidad)
    No bloquea la venta si el stock queda negativo.
    """
    movements: list[StockMovement] = []
    # Evitar doble descuento si se reintenta
    if StockMovement.objects.filter(order=order, reason=StockMovement.Reason.SALE_DEDUCT).exists():
        return movements

    items = order.items.select_related("menu_item").all()
    for order_item in items:
        menu_item = order_item.menu_item
        qty_sold = Decimal(order_item.quantity)

        recipe_lines = list(
            RecipeLine.objects.filter(menu_item=menu_item).select_related("stock_item")
        )
        if recipe_lines:
            for line in recipe_lines:
                delta = -(line.quantity * qty_sold)
                mov = apply_movement(
                    stock_item=line.stock_item,
                    reason=StockMovement.Reason.SALE_DEDUCT,
                    quantity_delta=delta,
                    user=user,
                    note=f"Orden #{order.pk} · {menu_item.name} ×{order_item.quantity}",
                    order=order,
                )
                movements.append(mov)
            continue

        # Producto unitario vinculado 1:1
        stock = None
        try:
            stock = menu_item.stock_item
        except StockItem.DoesNotExist:
            stock = None
        if stock is not None and stock.is_active:
            mov = apply_movement(
                stock_item=stock,
                reason=StockMovement.Reason.SALE_DEDUCT,
                quantity_delta=-qty_sold,
                user=user,
                note=f"Orden #{order.pk} · {menu_item.name} ×{order_item.quantity}",
                order=order,
            )
            movements.append(mov)

    return movements


def items_below_par():
    return (
        StockItem.objects.filter(is_active=True, par_level__gt=0)
        .filter(qty_on_hand__lt=F("par_level"))
        .order_by("name")
    )


def purchase_suggestions(days_cover: int = 5, lookback_days: int = 14):
    """
    Lista de compra enriquecida:
    - gap al par
    - proyección por consumo promedio diario (sale_deduct) * days_cover
    sugerido = max(gap_par, reorder_qty, proyección - on_hand)  (solo si > 0)
    """
    days_cover = max(1, int(days_cover))
    lookback_days = max(1, int(lookback_days))
    since = timezone.now() - timedelta(days=lookback_days)

    usage = {
        row["stock_item_id"]: abs(row["used"] or Decimal("0"))
        for row in (
            StockMovement.objects.filter(
                reason=StockMovement.Reason.SALE_DEDUCT,
                created_at__gte=since,
            )
            .values("stock_item_id")
            .annotate(used=Sum("quantity_delta"))
        )
    }

    rows = []
    for item in StockItem.objects.filter(is_active=True).order_by("name"):
        gap = item.suggested_buy_qty
        used = usage.get(item.pk, Decimal("0"))
        avg_daily = (used / Decimal(lookback_days)) if used else Decimal("0")
        projected_need = avg_daily * Decimal(days_cover)
        projection_buy = projected_need - item.qty_on_hand
        if projection_buy < 0:
            projection_buy = Decimal("0")

        suggested = gap
        if item.reorder_qty and item.reorder_qty > suggested:
            suggested = item.reorder_qty
        if projection_buy > suggested:
            suggested = projection_buy

        # Solo listar si hay algo que comprar o está bajo par
        if suggested <= 0 and not item.is_below_par:
            continue

        rows.append({
            "item": item,
            "gap_par": gap,
            "avg_daily_use": avg_daily,
            "projected_need": projected_need,
            "suggested_qty": suggested.quantize(Decimal("0.001")),
            "days_cover": days_cover,
            "lookback_days": lookback_days,
        })

    # Priorizar bajo par y mayor sugerido
    rows.sort(key=lambda r: (not r["item"].is_below_par, -r["suggested_qty"], r["item"].name))
    return rows


def waste_report(days: int = 30):
    since = timezone.now() - timedelta(days=max(1, int(days)))
    qs = StockMovement.objects.filter(created_at__gte=since).filter(
        Q(reason=StockMovement.Reason.WASTE)
        | Q(reason=StockMovement.Reason.COUNT_ADJUST, quantity_delta__lt=0)
    )
    by_item = (
        qs.values("stock_item_id", "stock_item__name", "stock_item__unit")
        .annotate(total_delta=Sum("quantity_delta"))
        .order_by("stock_item__name")
    )
    rows = []
    total_abs = Decimal("0")
    for row in by_item:
        delta = row["total_delta"] or Decimal("0")
        lost = abs(delta) if delta < 0 else Decimal("0")
        if lost <= 0:
            continue
        total_abs += lost
        rows.append({
            "name": row["stock_item__name"],
            "unit": row["stock_item__unit"],
            "lost": lost,
        })
    return {"rows": rows, "total_lost_units": total_abs, "days": days}
