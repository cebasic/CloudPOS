from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render

from apps.accounts.decorators import role_required
from apps.orders.models import Order


@login_required
@role_required("admin", "manager", "kitchen")
def kitchen_display(request):
    return render(request, "kitchen/display.html")


@login_required
@role_required("admin", "manager", "kitchen")
def kitchen_debug(request):
    orders = (
        Order.objects.filter(status__in=["pending", "in_progress", "ready"])
        .select_related("table", "waiter")
        .prefetch_related("items__menu_item")
        .order_by("created_at")
    )
    data = []
    for order in orders:
        items = []
        for item in order.items.all():
            items.append({
                "id": item.pk,
                "name": item.menu_item.name,
                "quantity": item.quantity,
                "notes": item.notes,
                "status": item.status,
            })
        data.append({
            "id": order.pk,
            "table": order.table.number,
            "order_status": order.status,
            "items": items,
        })
    return JsonResponse({"orders": data})
