from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from apps.accounts.decorators import role_required
from .forms import OrderForm, OrderItemForm, PaymentForm, DiscountForm
from .models import Order, OrderItem, Payment
from apps.tables.models import Table
from apps.cashier.models import CashSession


def _cash_session_open():
    return CashSession.objects.filter(status="open").exists()


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
            async_to_sync(channel_layer.group_send)(
                f"waiter_{order.waiter_id}",
                {
                    "type": "waiter.notification",
                    "order_id": order.pk,
                    "table_number": order.table.number,
                    "message": message or f"Orden #{order.pk} actualizada",
                },
            )
    except Exception:
        pass


@login_required
@role_required("admin", "manager", "waiter", "cashier")
def dashboard(request):
    active_orders = Order.objects.filter(
        status__in=["pending", "in_progress", "ready", "delivered"]
    ).select_related("table", "waiter").prefetch_related("items__menu_item")
    tables = Table.objects.all()
    return render(request, "orders/dashboard.html", {
        "active_orders": active_orders,
        "tables": tables,
        "cash_session_open": _cash_session_open(),
    })


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
        order.save()
        order.table.status = "occupied"
        order.table.save(update_fields=["status"])
        messages.success(request, f"Orden #{order.pk} creada para Mesa {order.table.number}.")
        return redirect("orders:detail", pk=order.pk)
    return render(request, "orders/order_form.html", {"form": form, "item_form": item_form, "title": "Nueva Orden"})


@login_required
@role_required("admin", "manager", "waiter", "cashier")
def order_detail(request, pk):
    order = get_object_or_404(
        Order.objects.select_related("table", "waiter").prefetch_related("items__menu_item"),
        pk=pk,
    )
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
    if order.status in ("closed", "cancelled"):
        messages.error(request, "No se puede modificar una orden cerrada o cancelada.")
        return redirect("orders:detail", pk=pk)
    form = OrderItemForm(request.POST)
    if form.is_valid():
        OrderItem.objects.create(
            order=order,
            menu_item=form.cleaned_data["menu_item"],
            quantity=form.cleaned_data["quantity"],
            notes=form.cleaned_data["notes"],
        )
        if order.status == "pending":
            order.status = "in_progress"
            order.save(update_fields=["status"])
        _notify_kitchen(order)
        messages.success(request, "Item agregado a la orden.")
    return redirect("orders:detail", pk=pk)


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
            has_active = Order.objects.filter(
                table=order.table,
                status__in=["pending", "in_progress", "ready", "delivered"],
            ).exclude(pk=order.pk).exists()
            if not has_active:
                order.table.status = "available"
                order.table.save(update_fields=["status"])
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

        if method == "cash" and amount_received:
            change_due = amount_received - final_total

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

        has_active = Order.objects.filter(
            table=order.table, status__in=["pending", "in_progress", "ready", "delivered"]
        ).exclude(pk=order.pk).exists()
        if not has_active:
            order.table.status = "available"
            order.table.save(update_fields=["status"])

        _notify_kitchen(order)

        if method == "cash" and change_due:
            messages.success(request, f"Orden #{order.pk} cobrada. Cambio: ${change_due:.2f}")
        else:
            messages.success(request, f"Orden #{order.pk} cobrada con {order.get_payment_method_display() if hasattr(order, 'get_payment_method_display') else method}.")
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
    return render(request, "orders/receipt.html", {"order": order})


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
            _notify_waiter(order, f"Mesa {order.table.number}: {item.menu_item.name} está listo")
    return redirect("orders:detail", pk=pk)
