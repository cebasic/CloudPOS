from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.decorators import role_required
from apps.menu.models import MenuItem

from .forms import (
    ManualAdjustForm,
    PurchaseForm,
    RecipeLineFormSet,
    StockCountForm,
    StockItemForm,
    WasteForm,
)
from .models import StockCount, StockCountLine, StockItem, StockMovement
from .services import (
    apply_movement,
    items_below_par,
    purchase_suggestions,
    register_manual_adjust,
    register_purchase,
    register_waste,
    waste_report,
)

_ROLES = ("admin", "manager")


@login_required
@role_required(*_ROLES)
def stock_list(request):
    items = StockItem.objects.select_related("menu_item").all()
    show = request.GET.get("show", "active")
    if show == "active":
        items = items.filter(is_active=True)
    elif show == "low":
        items = items_below_par()
    below_count = items_below_par().count()
    return render(request, "inventory/stock_list.html", {
        "items": items,
        "show": show,
        "below_count": below_count,
    })


@login_required
@role_required(*_ROLES)
def stock_create(request):
    form = StockItemForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        item = form.save()
        messages.success(request, f"Ítem «{item.name}» creado.")
        return redirect("inventory:detail", pk=item.pk)
    return render(request, "inventory/stock_form.html", {
        "form": form, "title": "Nuevo ítem de inventario",
    })


@login_required
@role_required(*_ROLES)
def stock_edit(request, pk):
    item = get_object_or_404(StockItem, pk=pk)
    form = StockItemForm(request.POST or None, instance=item)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Ítem actualizado.")
        return redirect("inventory:detail", pk=item.pk)
    return render(request, "inventory/stock_form.html", {
        "form": form, "title": f"Editar · {item.name}", "item": item,
    })


@login_required
@role_required(*_ROLES)
def stock_detail(request, pk):
    item = get_object_or_404(StockItem.objects.select_related("menu_item"), pk=pk)
    movements = item.movements.select_related("created_by", "order")[:40]
    return render(request, "inventory/stock_detail.html", {
        "item": item,
        "movements": movements,
        "purchase_form": PurchaseForm(),
        "adjust_form": ManualAdjustForm(),
        "waste_form": WasteForm(),
    })


@login_required
@role_required(*_ROLES)
def stock_purchase(request, pk):
    item = get_object_or_404(StockItem, pk=pk)
    form = PurchaseForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        register_purchase(
            stock_item=item,
            quantity=form.cleaned_data["quantity"],
            user=request.user,
            note=form.cleaned_data.get("note") or "",
        )
        messages.success(request, f"Compra registrada (+{form.cleaned_data['quantity']} {item.unit}).")
        return redirect("inventory:detail", pk=item.pk)
    return render(request, "inventory/purchase_form.html", {"form": form, "item": item})


@login_required
@role_required(*_ROLES)
def stock_adjust(request, pk):
    item = get_object_or_404(StockItem, pk=pk)
    form = ManualAdjustForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        register_manual_adjust(
            stock_item=item,
            quantity_delta=form.cleaned_data["quantity_delta"],
            user=request.user,
            note=form.cleaned_data.get("note") or "",
        )
        messages.success(request, "Ajuste manual registrado.")
        return redirect("inventory:detail", pk=item.pk)
    return render(request, "inventory/adjust_form.html", {"form": form, "item": item})


@login_required
@role_required(*_ROLES)
def stock_waste(request, pk):
    item = get_object_or_404(StockItem, pk=pk)
    form = WasteForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        register_waste(
            stock_item=item,
            quantity=form.cleaned_data["quantity"],
            user=request.user,
            note=form.cleaned_data.get("note") or "",
        )
        messages.success(request, "Merma registrada.")
        return redirect("inventory:detail", pk=item.pk)
    return render(request, "inventory/waste_form.html", {"form": form, "item": item})


@login_required
@role_required(*_ROLES)
def buy_list(request):
    days_cover = int(request.GET.get("days", 5) or 5)
    lookback = int(request.GET.get("lookback", 14) or 14)
    suggestions = purchase_suggestions(days_cover=days_cover, lookback_days=lookback)
    simple_below = items_below_par()
    return render(request, "inventory/buy_list.html", {
        "suggestions": suggestions,
        "simple_below": simple_below,
        "days_cover": days_cover,
        "lookback": lookback,
    })


@login_required
@role_required(*_ROLES)
def buy_list_csv(request):
    days_cover = int(request.GET.get("days", 5) or 5)
    lookback = int(request.GET.get("lookback", 14) or 14)
    suggestions = purchase_suggestions(days_cover=days_cover, lookback_days=lookback)
    lines = ["nombre,unidad,existencia,par,sugerido,consumo_diario_prom"]
    for row in suggestions:
        item = row["item"]
        lines.append(
            f"\"{item.name}\",{item.unit},{item.qty_on_hand},{item.par_level},"
            f"{row['suggested_qty']},{row['avg_daily_use']}"
        )
    content = "\n".join(lines) + "\n"
    response = HttpResponse(content, content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="lista_compras.csv"'
    return response


@login_required
@role_required(*_ROLES)
def recipe_edit(request, menu_item_id):
    menu_item = get_object_or_404(MenuItem, pk=menu_item_id)
    formset = RecipeLineFormSet(request.POST or None, instance=menu_item)
    if request.method == "POST" and formset.is_valid():
        formset.save()
        messages.success(request, f"Receta de «{menu_item.name}» guardada.")
        return redirect("inventory:recipe_edit", menu_item_id=menu_item.pk)
    return render(request, "inventory/recipe_form.html", {
        "menu_item": menu_item,
        "formset": formset,
    })


@login_required
@role_required(*_ROLES)
def recipe_index(request):
    dishes = MenuItem.objects.prefetch_related("recipe_lines__stock_item").order_by("name")
    return render(request, "inventory/recipe_index.html", {"dishes": dishes})


@login_required
@role_required(*_ROLES)
@transaction.atomic
def stock_count(request):
    items = list(StockItem.objects.filter(is_active=True).order_by("name"))
    form = StockCountForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        count = StockCount.objects.create(
            counted_by=request.user,
            notes=form.cleaned_data.get("notes") or "",
        )
        adjusted = 0
        for item in items:
            raw = request.POST.get(f"qty_{item.pk}", "").strip()
            if raw == "":
                continue
            try:
                counted = Decimal(raw.replace(",", "."))
            except (InvalidOperation, ValueError):
                messages.error(request, f"Cantidad inválida para {item.name}.")
                return redirect("inventory:count")
            diff = counted - item.qty_on_hand
            StockCountLine.objects.create(
                count=count,
                stock_item=item,
                qty_system=item.qty_on_hand,
                qty_counted=counted,
                difference=diff,
            )
            if diff != 0:
                apply_movement(
                    stock_item=item,
                    reason=StockMovement.Reason.COUNT_ADJUST,
                    quantity_delta=diff,
                    user=request.user,
                    note=f"Conteo #{count.pk}",
                )
                adjusted += 1
        messages.success(request, f"Conteo #{count.pk} guardado · {adjusted} ajuste(s).")
        return redirect("inventory:count_detail", pk=count.pk)

    return render(request, "inventory/count_form.html", {
        "items": items,
        "form": form,
    })


@login_required
@role_required(*_ROLES)
def stock_count_detail(request, pk):
    count = get_object_or_404(
        StockCount.objects.select_related("counted_by").prefetch_related("lines__stock_item"),
        pk=pk,
    )
    return render(request, "inventory/count_detail.html", {"count": count})


@login_required
@role_required(*_ROLES)
def waste_report_view(request):
    days = int(request.GET.get("days", 30) or 30)
    report = waste_report(days=days)
    return render(request, "inventory/waste_report.html", {"report": report, "days": days})
