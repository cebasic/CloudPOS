from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from apps.accounts.decorators import role_required
from .forms import TableForm
from .models import Table


@login_required
@role_required("admin", "manager")
def table_list(request):
    tables = Table.objects.all()
    return render(request, "tables/table_list.html", {"tables": tables})


@login_required
@role_required("admin", "manager")
def table_create(request):
    form = TableForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Mesa creada exitosamente.")
        return redirect("tables:list")
    return render(request, "tables/table_form.html", {"form": form, "title": "Nueva Mesa"})


@login_required
@role_required("admin", "manager")
def table_edit(request, pk):
    table = get_object_or_404(Table, pk=pk)
    form = TableForm(request.POST or None, instance=table)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Mesa actualizada exitosamente.")
        return redirect("tables:list")
    return render(request, "tables/table_form.html", {"form": form, "title": f"Editar Mesa {table.number}"})


@login_required
@role_required("admin", "manager")
def table_delete(request, pk):
    table = get_object_or_404(Table, pk=pk)
    if request.method == "POST":
        table.delete()
        messages.success(request, f"Mesa {table.number} eliminada.")
        return redirect("tables:list")
    return render(request, "tables/table_confirm_delete.html", {"table": table})
