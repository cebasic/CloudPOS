from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages

from apps.accounts.decorators import role_required
from .forms import BusinessSettingsForm
from .models import BusinessSettings


@login_required
@role_required("admin", "manager")
def business_editor(request):
    business = BusinessSettings.load()
    form = BusinessSettingsForm(
        request.POST or None,
        request.FILES or None,
        instance=business,
    )
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        obj.updated_by = request.user
        obj.save()
        messages.success(request, "Configuración del negocio actualizada.")
        return redirect("business:editor")
    return render(request, "business/editor.html", {"form": form, "business": business})
