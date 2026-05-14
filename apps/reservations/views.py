from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages

from apps.accounts.decorators import role_required
from .models import Reservation
from .forms import ReservationForm

_ROLES = ("admin", "manager", "waiter", "cashier")


@login_required
@role_required(*_ROLES)
def reservation_list(request):
    today = timezone.localdate()
    date_str = request.GET.get("date")
    if date_str:
        try:
            from datetime import date
            selected_date = date.fromisoformat(date_str)
        except ValueError:
            selected_date = today
    else:
        selected_date = today

    reservations = Reservation.objects.filter(date=selected_date).select_related("table", "created_by")
    upcoming = (
        Reservation.objects.filter(date__gt=today, status__in=["pending", "confirmed"])
        .select_related("table")
        .order_by("date", "time")[:10]
    )
    return render(request, "reservations/reservation_list.html", {
        "reservations": reservations,
        "selected_date": selected_date,
        "today": today,
        "upcoming": upcoming,
    })


@login_required
@role_required(*_ROLES)
def reservation_create(request):
    form = ReservationForm(request.POST or None)
    if request.GET.get("date"):
        form.initial["date"] = request.GET["date"]
    if request.method == "POST" and form.is_valid():
        reservation = form.save(commit=False)
        reservation.created_by = request.user
        reservation.save()
        messages.success(request, f"Reservación para {reservation.customer_name} creada.")
        return redirect("reservations:list")
    return render(request, "reservations/reservation_form.html", {
        "form": form, "title": "Nueva Reservación",
    })


@login_required
@role_required(*_ROLES)
def reservation_edit(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    form = ReservationForm(request.POST or None, instance=reservation)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Reservación actualizada.")
        return redirect("reservations:list")
    return render(request, "reservations/reservation_form.html", {
        "form": form, "title": f"Editar: {reservation.customer_name}",
    })


@login_required
@role_required(*_ROLES)
def reservation_status(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    new_status = request.POST.get("status")
    if new_status and new_status in dict(Reservation.Status.choices):
        reservation.status = new_status
        reservation.save(update_fields=["status"])
        messages.success(request, f"Reservación de {reservation.customer_name} marcada como {reservation.get_status_display()}.")
    return redirect("reservations:list")
