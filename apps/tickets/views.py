from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages

from apps.accounts.decorators import role_required
from .forms import TicketSettingsForm
from .models import TicketSettings


@login_required
@role_required("admin", "manager")
def ticket_editor(request):
    ticket = TicketSettings.load()
    form = TicketSettingsForm(
        request.POST or None,
        request.FILES or None,
        instance=ticket,
    )
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        obj.updated_by = request.user
        obj.save()
        messages.success(request, "Ticket actualizado correctamente.")
        return redirect("tickets:editor")
    return render(request, "tickets/editor.html", {"form": form, "ticket": ticket})
