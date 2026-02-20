import json
from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, F
from django.db.models.functions import TruncDate
from django.shortcuts import render
from django.utils import timezone

from apps.accounts.decorators import role_required
from apps.orders.models import Order, OrderItem


@login_required
@role_required("admin", "manager")
def report_index(request):
    date_from = request.GET.get("date_from")
    date_to = request.GET.get("date_to")

    today = timezone.localdate()
    if date_from:
        date_from = datetime.strptime(date_from, "%Y-%m-%d").date()
    else:
        date_from = today - timedelta(days=30)

    if date_to:
        date_to = datetime.strptime(date_to, "%Y-%m-%d").date()
    else:
        date_to = today

    orders = Order.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to,
        status__in=["delivered", "closed"],
    )

    total_orders = orders.count()
    total_revenue = OrderItem.objects.filter(
        order__in=orders,
    ).aggregate(
        total=Sum(F("menu_item__price") * F("quantity"))
    )["total"] or 0

    avg_ticket = (total_revenue / total_orders) if total_orders > 0 else 0

    top_items = (
        OrderItem.objects.filter(order__in=orders)
        .values("menu_item__name")
        .annotate(
            total_qty=Sum("quantity"),
            total_revenue=Sum(F("menu_item__price") * F("quantity")),
        )
        .order_by("-total_qty")[:10]
    )

    orders_by_waiter = (
        orders.values("waiter__username", "waiter__first_name", "waiter__last_name")
        .annotate(order_count=Count("id"))
        .order_by("-order_count")
    )

    daily_sales = list(
        orders.annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(count=Count("id"))
        .order_by("day")
    )

    daily_sales_json = json.dumps(
        [{"day": str(d["day"]), "count": d["count"]} for d in daily_sales]
    )

    context = {
        "date_from": date_from,
        "date_to": date_to,
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "avg_ticket": avg_ticket,
        "top_items": top_items,
        "orders_by_waiter": orders_by_waiter,
        "daily_sales_json": daily_sales_json,
    }
    return render(request, "reports/index.html", context)
