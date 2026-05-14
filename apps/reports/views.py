import csv
import json
from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, F, Q
from django.db.models.functions import TruncDate, TruncHour
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from apps.accounts.decorators import role_required
from apps.orders.models import Order, OrderItem, Payment


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

    payments = Payment.objects.filter(order__in=orders)

    total_orders = orders.count()
    total_revenue = payments.aggregate(t=Sum("total"))["t"] or 0
    total_tips = payments.aggregate(t=Sum("tip"))["t"] or 0
    avg_ticket = (total_revenue / total_orders) if total_orders > 0 else 0

    # Discount stats
    discounted_orders = orders.exclude(discount_type="none")
    total_discounts = sum(o.discount_amount for o in discounted_orders)

    # Cancellations
    cancelled = Order.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to,
        status="cancelled",
    ).count()
    all_orders_count = Order.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to,
    ).count()
    cancel_rate = (cancelled / all_orders_count * 100) if all_orders_count > 0 else 0

    # Payment method breakdown
    cash_revenue = (
        (payments.filter(method="cash").aggregate(t=Sum("total"))["t"] or 0) +
        (payments.filter(method="mixed").aggregate(t=Sum("cash_amount"))["t"] or 0)
    )
    card_revenue = (
        (payments.filter(method="card").aggregate(t=Sum("total"))["t"] or 0) +
        (payments.filter(method="mixed").aggregate(t=Sum("card_amount"))["t"] or 0)
    )
    mixed_count = payments.filter(method="mixed").count()

    # Top items
    top_items = (
        OrderItem.objects.filter(order__in=orders)
        .values("menu_item__name")
        .annotate(
            total_qty=Sum("quantity"),
            total_revenue=Sum(F("menu_item__price") * F("quantity")),
        )
        .order_by("-total_qty")[:10]
    )

    # By waiter
    orders_by_waiter = (
        orders.values("waiter__username", "waiter__first_name", "waiter__last_name")
        .annotate(order_count=Count("id"))
        .order_by("-order_count")
    )

    # Daily sales chart
    daily_sales = list(
        orders.annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(count=Count("id"), revenue=Sum("payment__total"))
        .order_by("day")
    )
    daily_sales_json = json.dumps(
        [{"day": str(d["day"]), "count": d["count"], "revenue": float(d["revenue"] or 0)} for d in daily_sales]
    )

    # Hourly distribution (today or single day selected)
    if date_from == date_to:
        hourly = list(
            orders.annotate(hour=TruncHour("created_at"))
            .values("hour")
            .annotate(count=Count("id"))
            .order_by("hour")
        )
        hourly_json = json.dumps([{"hour": h["hour"].strftime("%H:00"), "count": h["count"]} for h in hourly])
    else:
        hourly_json = json.dumps([])

    context = {
        "date_from": date_from,
        "date_to": date_to,
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "total_tips": total_tips,
        "total_discounts": total_discounts,
        "avg_ticket": avg_ticket,
        "cancel_rate": cancel_rate,
        "cancelled": cancelled,
        "cash_revenue": cash_revenue,
        "card_revenue": card_revenue,
        "mixed_count": mixed_count,
        "top_items": top_items,
        "orders_by_waiter": orders_by_waiter,
        "daily_sales_json": daily_sales_json,
        "hourly_json": hourly_json,
        "single_day": date_from == date_to,
    }
    return render(request, "reports/index.html", context)


@login_required
@role_required("admin", "manager")
def report_export_csv(request):
    date_from_str = request.GET.get("date_from")
    date_to_str = request.GET.get("date_to")
    today = timezone.localdate()
    date_from = datetime.strptime(date_from_str, "%Y-%m-%d").date() if date_from_str else today - timedelta(days=30)
    date_to = datetime.strptime(date_to_str, "%Y-%m-%d").date() if date_to_str else today

    orders = Order.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to,
        status__in=["delivered", "closed"],
    ).select_related("table", "waiter", "payment").prefetch_related("items__menu_item")

    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="reporte_{date_from}_{date_to}.csv"'
    response.write("﻿")  # BOM for Excel

    writer = csv.writer(response)
    writer.writerow(["Orden", "Mesa", "Mesero", "Fecha", "Hora", "Estado", "Método Pago", "Subtotal", "Descuento", "Total", "Propina"])

    for order in orders:
        pmt = order.payment if hasattr(order, "payment") else None
        writer.writerow([
            order.pk,
            order.table.number,
            order.waiter.get_full_name() or order.waiter.username,
            order.created_at.strftime("%Y-%m-%d"),
            order.created_at.strftime("%H:%M"),
            order.get_status_display(),
            pmt.get_method_display() if pmt else "-",
            order.subtotal,
            order.discount_amount,
            order.final_total,
            pmt.tip if pmt else 0,
        ])

    return response
