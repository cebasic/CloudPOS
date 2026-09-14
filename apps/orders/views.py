from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from apps.accounts.decorators import role_required
from .forms import OrderForm, OrderItemForm, PaymentForm, DiscountForm, TakeoutOrderForm
from .models import Order, OrderItem, Payment
from apps.tables.models import Table
from apps.cashier.models import CashSession


def _cash_session_open():
    return CashSession.objects.filter(status="open").exists()


def _release_table_if_idle(order):
    if not order.table_id:
        return
    has_active = Order.objects.filter(
        table_id=order.table_id,
        status__in=["pending", "in_progress", "ready", "delivered"],
    ).exclude(pk=order.pk).exists()
    if not has_active and order.table_id:
        Table.objects.filter(pk=order.table_id).update(status="available")


def _notify_kitchen(order):
    try:
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                "kitchen",
                {"type": "kitchen.update", "order_id": order.pk},
            )
    except Exception:
        pass


def _notify_waiter(order, message=None):
    try:
        channel_layer = get_channel_layer()
        if channel_layer:
            label = order.display_label
            async_to_sync(channel_layer.group_send)(
                f"waiter_{order.waiter_id}",
                {
                    "type": "waiter.notification",
                    "order_id": order.pk,
                    "table_number": label,
                    "message": message or f"Orden #{order.pk} actualizada",
                },
            )
            if order.is_togo:
                async_to_sync(channel_layer.group_send)(
                    "cashier_station",
                    {
                        "type": "bill.request",
                        "order_id": order.pk,
                        "table_number": label,
                        "message": message or f"{label}: platillo listo",
                    },
                )
    except Exception:
        pass


def _notify_cashier_bill(order):
    """Avisa a la(s) estación(es) de caja que una orden pidió su cuenta."""
    try:
        channel_layer = get_channel_layer()
        if channel_layer:
            label = order.display_label
            async_to_sync(channel_layer.group_send)(
                "cashier_station",
                {
                    "type": "bill.request",
                    "order_id": order.pk,
                    "table_number": label,
                    "message": f"{label} solicitó su cuenta",
                },
            )
    except Exception:
        pass


@login_required
@role_required("admin", "manager", "waiter", "cashier")
def order_request_bill(request, pk):
    """El mesero pide imprimir la cuenta → notifica a la estación de caja."""
    order = get_object_or_404(Order.objects.select_related("table"), pk=pk)
    if order.status in ("closed", "cancelled"):
        messages.error(request, "Esta orden ya no está activa.")
        return redirect("orders:detail", pk=pk)
    _notify_cashier_bill(order)
    messages.success(request, f"Cuenta de {order.display_label} enviada a caja.")
    return redirect("orders:detail", pk=pk)


@login_required
@role_required("admin", "manager", "waiter", "cashier")
def order_bill(request, pk):
    """Pre-cuenta imprimible (antes de pagar). La caja la abre e imprime."""
    order = get_object_or_404(
        Order.objects.select_related("table", "waiter").prefetch_related("items__menu_item"),
        pk=pk,
    )
    return render(request, "orders/bill.html", {"order": order})


@login_required
@role_required("admin", "manager", "waiter", "cashier")
def dashboard(request):
    active_orders = Order.objects.filter(
        status__in=["pending", "in_progress", "ready", "delivered"]
    ).select_related("table", "waiter").prefetch_related("items__menu_item")
    # Meseros solo ven mesas; para llevar es de caja
    if request.user.role == "waiter":
        active_orders = active_orders.filter(order_type=Order.OrderType.DINE_IN)
    tables = Table.objects.all()
    return render(request, "orders/dashboard.html", {
        "active_orders": active_orders,
        "tables": tables,
        "occupied_count": tables.filter(status="occupied").count(),
        "available_count": tables.filter(status="available").count(),
        "ready_count": active_orders.filter(status="ready").count(),
        "cash_session_open": _cash_session_open(),
        "can_create_togo": request.user.role in ("admin", "manager", "cashier"),
    })


def _waiter_blocked_from_togo(request, order):
    if order.is_togo and getattr(request.user, "role", None) == "waiter":
        messages.error(request, "Los pedidos para llevar los atiende caja.")
        return True
    return False


@login_required
@role_required("admin", "manager", "waiter", "cashier")
def order_create(request):
    if not _cash_session_open():
        messages.error(request, "No se puede crear una orden: la caja no está abierta.")
        return redirect("orders:dashboard")

    initial = {}
    table_id = request.GET.get("table")
    if table_id:
        initial["table"] = table_id
    form = OrderForm(request.POST or None, initial=initial)
    item_form = OrderItemForm()
    if request.method == "POST" and form.is_valid():
        order = form.save(commit=False)
        order.waiter = request.user
        order.order_type = Order.OrderType.DINE_IN
        order.save()
        order.table.status = "occupied"
        order.table.save(update_fields=["status"])
        messages.success(request, f"Orden #{order.pk} creada para Mesa {order.table.number}.")
        return redirect("orders:detail", pk=order.pk)
    return render(request, "orders/order_form.html", {"form": form, "item_form": item_form, "title": "Nueva Orden"})


@login_required
@role_required("admin", "manager", "cashier")
def order_create_togo(request):
    """Para llevar / domicilio — solo caja, admin y gerente."""
    if not _cash_session_open():
        messages.error(request, "No se puede crear un pedido para llevar: la caja no está abierta.")
        return redirect("cashier:dashboard")

    form = TakeoutOrderForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        order = form.save(commit=False)
        order.waiter = request.user
        order.table = None
        order.save()
        messages.success(request, f"Pedido #{order.pk} · {order.display_label} creado.")
        return redirect("orders:detail", pk=order.pk)
    return render(request, "orders/togo_form.html", {
        "form": form,
        "title": "Para llevar",
    })


@login_required
@role_required("admin", "manager", "waiter", "cashier")
def order_detail(request, pk):
    order = get_object_or_404(
        Order.objects.select_related("table", "waiter").prefetch_related("items__menu_item"),
        pk=pk,
    )
    if _waiter_blocked_from_togo(request, order):
        return redirect("orders:dashboard")
    item_form = OrderItemForm()
    return render(request, "orders/order_detail.html", {"order": order, "item_form": item_form})


@login_required
@role_required("admin", "manager", "waiter", "cashier")
def order_items_partial(request, pk):
    order = get_object_or_404(
        Order.objects.prefetch_related("items__menu_item"),
        pk=pk,
    )
    return render(request, "orders/partials/items_table.html", {"order": order})


@login_required
@role_required("admin", "manager", "waiter", "cashier")
def order_add_item(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if _waiter_blocked_from_togo(request, order):
        return redirect("orders:dashboard")
    if order.status in ("closed", "cancelled"):
        messages.error(request, "No se puede modificar una orden cerrada o cancelada.")
        return redirect("orders:detail", pk=pk)
    form = OrderItemForm(request.POST)
    keep_cat = (request.POST.get("keep_cat") or "").strip()
    if form.is_valid():
        menu_item = form.cleaned_data["menu_item"]
        initial_status = (
            OrderItem.Status.DELIVERED
            if not menu_item.requires_kitchen
            else OrderItem.Status.PENDING
        )
        OrderItem.objects.create(
            order=order,
            menu_item=menu_item,
            quantity=form.cleaned_data["quantity"],
            notes=form.cleaned_data["notes"],
            status=initial_status,
        )
        if order.status == "pending" and menu_item.requires_kitchen:
            order.status = "in_progress"
            order.save(update_fields=["status"])
        order.sync_status()
        if menu_item.requires_kitchen:
            _notify_kitchen(order)
        messages.success(
            request,
            "Item agregado a la orden."
            if menu_item.requires_kitchen
            else f"{menu_item.name} agregado (lo sirve el mesero, no va a cocina).",
        )
    url = reverse("orders:detail", kwargs={"pk": pk})
    if keep_cat:
        url = f"{url}?cat={keep_cat}"
    return redirect(url)


@login_required
@role_required("admin", "manager", "waiter", "cashier")
def order_remove_item(request, pk, item_pk):
    order = get_object_or_404(Order, pk=pk)
    item = get_object_or_404(OrderItem, pk=item_pk, order=order)
    if request.method == "POST":
        item.delete()
        _notify_kitchen(order)
        messages.success(request, "Item eliminado.")
    return redirect("orders:detail", pk=pk)


@login_required
@role_required("admin", "manager", "waiter", "cashier")
def order_update_status(request, pk):
    order = get_object_or_404(Order, pk=pk)
    new_status = request.POST.get("status")
    if new_status == "closed":
        return redirect("orders:checkout", pk=pk)
    if new_status and new_status in dict(Order.Status.choices):
        order.status = new_status
        order.save(update_fields=["status", "updated_at"])
        if new_status == "cancelled":
            _release_table_if_idle(order)
        _notify_kitchen(order)
        messages.success(request, f"Orden #{order.pk} actualizada a {order.get_status_display()}.")
    return redirect("orders:detail", pk=pk)


@login_required
@role_required("admin", "manager", "cashier")
@transaction.atomic
def order_apply_discount(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if order.status in ("closed", "cancelled"):
        messages.error(request, "No se puede aplicar descuento a una orden cerrada o cancelada.")
        return redirect("orders:detail", pk=pk)
    form = DiscountForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        order.discount_type = form.cleaned_data["discount_type"]
        order.discount_value = form.cleaned_data["discount_value"]
        order.discount_reason = form.cleaned_data["discount_reason"]
        order.discount_by = request.user
        order.save(update_fields=["discount_type", "discount_value", "discount_reason", "discount_by"])
        messages.success(request, f"Descuento aplicado a orden #{order.pk}.")
        return redirect("orders:detail", pk=pk)
    return render(request, "orders/discount_form.html", {"form": form, "order": order})


@login_required
@role_required("admin", "manager", "waiter", "cashier")
@transaction.atomic
def order_checkout(request, pk):
    order = get_object_or_404(
        Order.objects.select_related("table", "waiter").prefetch_related("items__menu_item"),
        pk=pk,
    )
    if order.status == "closed":
        messages.info(request, "Esta orden ya fue cobrada.")
        return redirect("orders:detail", pk=pk)
    if hasattr(order, "payment"):
        messages.info(request, "Esta orden ya tiene un pago registrado.")
        return redirect("orders:detail", pk=pk)

    final_total = order.final_total
    form = PaymentForm(request.POST or None, order_total=final_total)

    if request.method == "POST" and form.is_valid():
        method = form.cleaned_data["method"]
        amount_received = form.cleaned_data.get("amount_received")
        tip = form.cleaned_data.get("tip") or 0
        cash_amount = form.cleaned_data.get("cash_amount")
        card_amount = form.cleaned_data.get("card_amount")
        change_due = None
        due_total = final_total + tip

        if method == "cash" and amount_received is not None:
            change_due = amount_received - due_total

        Payment.objects.create(
            order=order,
            method=method,
            total=final_total,
            tip=tip,
            amount_received=amount_received if method == "cash" else None,
            change_due=change_due,
            cash_amount=cash_amount if method == "mixed" else None,
            card_amount=card_amount if method == "mixed" else None,
            collected_by=request.user,
        )

        order.status = "closed"
        order.save(update_fields=["status", "updated_at"])

        # Inventario: descuento por receta / vínculo 1:1 (no bloquea cobro)
        try:
            from apps.inventory.services import deduct_for_order
            inv_moves = deduct_for_order(order, user=request.user)
            low = [
                m.stock_item.name
                for m in inv_moves
                if m.stock_item.par_level > 0 and m.qty_after < m.stock_item.par_level
            ]
            if low:
                messages.warning(
                    request,
                    "Stock bajo después del cobro: " + ", ".join(sorted(set(low))[:8]),
                )
        except Exception:
            # Nunca tumbar el cobro por un fallo de inventario
            messages.warning(request, "Cobro OK, pero no se pudo actualizar el inventario.")

        _release_table_if_idle(order)
        _notify_kitchen(order)

        if method == "cash" and change_due is not None:
            messages.success(request, f"Orden #{order.pk} cobrada. Cambio: ${change_due:.2f}")
        else:
            messages.success(request, f"Orden #{order.pk} cobrada.")
        return redirect("orders:receipt", pk=pk)

    return render(request, "orders/checkout.html", {
        "order": order,
        "form": form,
        "order_total": final_total,
        "order_total_js": str(float(final_total)),
    })


@login_required
@role_required("admin", "manager", "waiter", "cashier")
def order_receipt(request, pk):
    order = get_object_or_404(
        Order.objects.select_related("table", "waiter", "payment").prefetch_related("items__menu_item"),
        pk=pk,
    )
    next_url = (request.GET.get("next") or "").strip()
    # Solo rutas internas relativas (anti open-redirect)
    if not (next_url.startswith("/") and not next_url.startswith("//")):
        next_url = ""
    return render(request, "orders/receipt.html", {
        "order": order,
        "receipt_next": next_url,
    })


@login_required
@role_required("admin", "manager", "waiter", "cashier")
def order_item_status(request, pk, item_pk):
    order = get_object_or_404(Order.objects.select_related("table"), pk=pk)
    item = get_object_or_404(OrderItem, pk=item_pk, order=order)
    new_status = request.POST.get("status")
    if new_status and new_status in dict(OrderItem.Status.choices):
        item.status = new_status
        item.save(update_fields=["status"])
        order.sync_status()
        _notify_kitchen(order)
        if new_status == "ready":
            _notify_waiter(order, f"{order.display_label}: {item.menu_item.name} está listo")
    return redirect("orders:detail", pk=pk)
