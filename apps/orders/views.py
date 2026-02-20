from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from apps.accounts.decorators import role_required
from .forms import OrderForm, OrderItemForm, PaymentForm
from .models import Order, OrderItem, Payment
from apps.tables.models import Table


def _notify_kitchen(order):
    try:
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                "kitchen",
                {
                    "type": "kitchen.update",
                    "order_id": order.pk,
                },
            )
    except Exception:
        pass


@login_required
@role_required("admin", "manager", "waiter")
def dashboard(request):
    active_orders = Order.objects.filter(
        status__in=["pending", "in_progress", "ready", "delivered"]
    ).select_related("table", "waiter").prefetch_related("items__menu_item")
    tables = Table.objects.all()
    return render(request, "orders/dashboard.html", {
        "active_orders": active_orders,
        "tables": tables,
    })


@login_required
@role_required("admin", "manager", "waiter")
def order_create(request):
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
@role_required("admin", "manager", "waiter")
def order_detail(request, pk):
    order = get_object_or_404(
        Order.objects.select_related("table", "waiter").prefetch_related("items__menu_item"),
        pk=pk,
    )
    item_form = OrderItemForm()
    return render(request, "orders/order_detail.html", {"order": order, "item_form": item_form})


@login_required
@role_required("admin", "manager", "waiter")
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
@role_required("admin", "manager", "waiter")
def order_remove_item(request, pk, item_pk):
    order = get_object_or_404(Order, pk=pk)
    item = get_object_or_404(OrderItem, pk=item_pk, order=order)
    if request.method == "POST":
        item.delete()
        _notify_kitchen(order)
        messages.success(request, "Item eliminado.")
    return redirect("orders:detail", pk=pk)


@login_required
@role_required("admin", "manager", "waiter")
def order_update_status(request, pk):
    order = get_object_or_404(Order, pk=pk)
    new_status = request.POST.get("status")
    if new_status == "closed":
        return redirect("orders:checkout", pk=pk)
    if new_status and new_status in dict(Order.Status.choices):
        order.status = new_status
        order.save(update_fields=["status", "updated_at"])
        _notify_kitchen(order)
        messages.success(request, f"Orden #{order.pk} actualizada a {order.get_status_display()}.")
    return redirect("orders:detail", pk=pk)


@login_required
@role_required("admin", "manager", "waiter")
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

    order_total = order.total
    form = PaymentForm(request.POST or None, order_total=order_total)

    if request.method == "POST" and form.is_valid():
        method = form.cleaned_data["method"]
        amount_received = form.cleaned_data.get("amount_received")
        change_due = None

        if method == "cash" and amount_received:
            change_due = amount_received - order_total

        Payment.objects.create(
            order=order,
            method=method,
            total=order_total,
            amount_received=amount_received if method == "cash" else None,
            change_due=change_due,
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
            messages.success(request, f"Orden #{order.pk} cobrada con {form.cleaned_data['method']}.")
        return redirect("orders:receipt", pk=pk)

    return render(request, "orders/checkout.html", {
        "order": order,
        "form": form,
        "order_total": order_total,
        "order_total_js": str(float(order_total)),
    })


@login_required
@role_required("admin", "manager", "waiter")
def order_receipt(request, pk):
    order = get_object_or_404(
        Order.objects.select_related("table", "waiter", "payment").prefetch_related("items__menu_item"),
        pk=pk,
    )
    return render(request, "orders/receipt.html", {"order": order})


@login_required
@role_required("admin", "manager", "waiter")
def order_item_status(request, pk, item_pk):
    order = get_object_or_404(Order, pk=pk)
    item = get_object_or_404(OrderItem, pk=item_pk, order=order)
    new_status = request.POST.get("status")
    if new_status and new_status in dict(OrderItem.Status.choices):
        item.status = new_status
        item.save(update_fields=["status"])
        order.sync_status()
        _notify_kitchen(order)
    return redirect("orders:detail", pk=pk)
