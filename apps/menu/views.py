from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse

from apps.accounts.decorators import role_required
from .forms import CategoryForm, MenuItemForm
from .models import Category, MenuItem


@login_required
@role_required("admin", "manager")
def category_list(request):
    categories = Category.objects.prefetch_related("items").all()
    return render(request, "menu/category_list.html", {"categories": categories})


@login_required
@role_required("admin", "manager")
def category_create(request):
    form = CategoryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Categoria creada exitosamente.")
        return redirect("menu:category_list")
    return render(request, "menu/category_form.html", {"form": form, "title": "Nueva Categoria"})


@login_required
@role_required("admin", "manager")
def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    form = CategoryForm(request.POST or None, instance=category)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Categoria actualizada.")
        return redirect("menu:category_list")
    return render(request, "menu/category_form.html", {"form": form, "title": f"Editar: {category.name}"})


@login_required
@role_required("admin", "manager")
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == "POST":
        category.delete()
        messages.success(request, f"Categoria '{category.name}' eliminada.")
        return redirect("menu:category_list")
    return render(request, "menu/category_confirm_delete.html", {"category": category})


@login_required
@role_required("admin", "manager")
def item_create(request):
    form = MenuItemForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Platillo creado exitosamente.")
        return redirect("menu:category_list")
    return render(request, "menu/item_form.html", {"form": form, "title": "Nuevo Platillo"})


@login_required
@role_required("admin", "manager")
def item_edit(request, pk):
    item = get_object_or_404(MenuItem, pk=pk)
    form = MenuItemForm(request.POST or None, request.FILES or None, instance=item)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Platillo actualizado.")
        return redirect("menu:category_list")
    return render(request, "menu/item_form.html", {"form": form, "title": f"Editar: {item.name}"})


@login_required
@role_required("admin", "manager")
def item_delete(request, pk):
    item = get_object_or_404(MenuItem, pk=pk)
    if request.method == "POST":
        item.delete()
        messages.success(request, f"Platillo '{item.name}' eliminado.")
        return redirect("menu:category_list")
    return render(request, "menu/item_confirm_delete.html", {"item": item})


@login_required
@role_required("admin", "manager")
def item_toggle_available(request, pk):
    item = get_object_or_404(MenuItem, pk=pk)
    item.available = not item.available
    item.save(update_fields=["available"])
    if request.htmx:
        if item.available:
            badge = '<span class="inline-flex items-center rounded-full px-2 py-1 text-xs font-medium bg-emerald-500/10 text-emerald-400">Disponible</span>'
        else:
            badge = '<span class="inline-flex items-center rounded-full px-2 py-1 text-xs font-medium bg-red-500/10 text-red-400">No disponible</span>'
        return HttpResponse(badge)
    return redirect("menu:category_list")


@login_required
@role_required("admin", "manager", "kitchen")
def quick_86(request):
    categories = Category.objects.prefetch_related("items").all()
    if request.method == "POST" and request.htmx:
        item_id = request.POST.get("item_id")
        item = get_object_or_404(MenuItem, pk=item_id)
        if request.user.role in ("admin", "manager", "kitchen"):
            item.available = not item.available
            item.save(update_fields=["available"])
        if item.available:
            badge = '<span class="inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold bg-emerald-500/10 text-emerald-400 ring-1 ring-emerald-500/20">Disponible</span>'
        else:
            badge = '<span class="inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold bg-red-500/10 text-red-400 ring-1 ring-red-500/20">86\'d</span>'
        return HttpResponse(badge)
    return render(request, "menu/quick_86.html", {"categories": categories})
