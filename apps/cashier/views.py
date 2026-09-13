from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages

from apps.accounts.decorators import role_required
from .models import CashSession, CashCut, Expense
from .forms import OpenSessionForm, CashCutForm, ExpenseForm
from apps.orders.models import Order, Payment

_ROLES = ("admin", "manager", "cashier")


def _open_session():
    return CashSession.objects.filter(status="open").first()


def _session_payments(session):
    """Pagos de la sesión (misma ventana que el corte)."""
    qs = Payment.objects.filter(created_at__gte=session.opened_at)
    if session.closed_at:
        qs = qs.filter(created_at__lte=session.closed_at)
    return (
        qs.select_related(
            "order",
            "order__table",
            "order__waiter",
            "collected_by",
        )
        .prefetch_related("order__items__menu_item")
        .order_by("-created_at")
    )


@login_required
@role_required(*_ROLES)
def dashboard(request):
    session = _open_session()
    recent_cuts = CashCut.objects.select_related(
        "cut_by", "session", "session__opened_by"
    ).order_by("-created_at")[:8]
    recent_sessions = CashSession.objects.select_related(
        "opened_by", "closed_by"
    ).order_by("-opened_at")[:6]
    expenses = session.expenses.select_related("created_by").all() if session else []
    togo_orders = (
        Order.objects.filter(
            order_type__in=[Order.OrderType.PICKUP, Order.OrderType.DELIVERY],
            status__in=["pending", "in_progress", "ready", "delivered"],
        )
        .select_related("waiter")
        .prefetch_related("items__menu_item")
        .order_by("created_at")
    )
    recent_tickets = list(_session_payments(session)[:6]) if session else []
    return render(request, "cashier/dashboard.html", {
        "session": session,
        "recent_cuts": recent_cuts,
        "recent_sessions": recent_sessions,
        "expenses": expenses,
        "togo_orders": togo_orders,
        "recent_tickets": recent_tickets,
    })


@login_required
@role_required(*_ROLES)
def session_open(request):
    if _open_session():
        messages.warning(request, "Ya hay una sesión de caja abierta.")
        return redirect("cashier:dashboard")

    form = OpenSessionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        CashSession.objects.create(
            opened_by=request.user,
            initial_cash=form.cleaned_data["initial_cash"],
            notes=form.cleaned_data.get("notes", ""),
        )
        messages.success(
            request,
            f"Caja abierta con fondo de ${form.cleaned_data['initial_cash']:.2f}.",
        )
        return redirect("cashier:dashboard")

    return render(request, "cashier/session_open.html", {"form": form})


@login_required
@role_required(*_ROLES)
def cash_cut(request):
    session = _open_session()
    if not session:
        messages.error(request, "No hay sesión de caja abierta.")
        return redirect("cashier:dashboard")

    cash_sales = session.cash_sales()
    card_sales = session.card_sales()
    change_given = session.change_given()
    cash_expected = session.expected_in_drawer()
    order_count = session.order_count()
    total_sales = cash_sales + card_sales
    total_tips = session.total_tips()
    total_expenses = session.total_expenses()

    form = CashCutForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        cash_counted = form.cleaned_data["cash_counted"]
        cut_type = form.cleaned_data["cut_type"]

        cut = CashCut.objects.create(
            session=session,
            cut_by=request.user,
            cut_type=cut_type,
            initial_cash=session.initial_cash,
            cash_sales=cash_sales,
            card_sales=card_sales,
            change_given=change_given,
            order_count=order_count,
            total_tips=total_tips,
            total_expenses=total_expenses,
            cash_counted=cash_counted,
            cash_expected=cash_expected,
            cash_difference=cash_counted - cash_expected,
            notes=form.cleaned_data.get("notes", ""),
        )

        if cut_type == "final":
            session.status = "closed"
            session.closed_by = request.user
            session.closed_at = timezone.now()
            session.save()
            messages.success(request, "Corte final realizado. Sesión de caja cerrada.")
        else:
            messages.success(request, "Corte parcial registrado correctamente.")

        return redirect("cashier:cut_detail", pk=cut.pk)

    return render(request, "cashier/cash_cut.html", {
        "session": session,
        "form": form,
        "cash_sales": cash_sales,
        "card_sales": card_sales,
        "change_given": change_given,
        "cash_expected": cash_expected,
        "order_count": order_count,
        "total_sales": total_sales,
        "total_tips": total_tips,
        "total_expenses": total_expenses,
    })


@login_required
@role_required(*_ROLES)
def cut_detail(request, pk):
    cut = get_object_or_404(
        CashCut.objects.select_related("cut_by", "session", "session__opened_by"),
        pk=pk,
    )
    return render(request, "cashier/cut_detail.html", {"cut": cut})


@login_required
@role_required(*_ROLES)
def expense_create(request):
    session = _open_session()
    if not session:
        messages.error(request, "No hay sesión de caja abierta para registrar un gasto.")
        return redirect("cashier:dashboard")
    form = ExpenseForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        expense = form.save(commit=False)
        expense.session = session
        expense.created_by = request.user
        expense.save()
        messages.success(request, f"Gasto de ${expense.amount} registrado.")
        return redirect("cashier:dashboard")
    return render(request, "cashier/expense_form.html", {"form": form, "session": session})


@login_required
@role_required(*_ROLES)
def history(request):
    cuts = CashCut.objects.select_related(
        "cut_by", "session", "session__opened_by"
    ).order_by("-created_at")
    sessions = CashSession.objects.select_related(
        "opened_by", "closed_by"
    ).order_by("-opened_at")[:30]
    return render(request, "cashier/history.html", {
        "cuts": cuts,
        "sessions": sessions,
    })


@login_required
@role_required(*_ROLES)
def tickets(request):
    """Historial de tickets cobrados para reimprimir (sesión actual o elegida)."""
    sessions = list(
        CashSession.objects.select_related("opened_by").order_by("-opened_at")[:20]
    )
    open_session = _open_session()
    session_id = request.GET.get("session")
    session = None
    if session_id:
        session = get_object_or_404(CashSession, pk=session_id)
    elif open_session:
        session = open_session
    elif sessions:
        session = sessions[0]

    payments = _session_payments(session) if session else Payment.objects.none()
    q = (request.GET.get("q") or "").strip()
    if q:
        filt = (
            Q(order__customer_name__icontains=q)
            | Q(order__customer_phone__icontains=q)
        )
        if q.isdigit():
            filt = filt | Q(order_id=int(q)) | Q(order__table__number=int(q))
        payments = payments.filter(filt)

    return render(request, "cashier/tickets.html", {
        "session": session,
        "sessions": sessions,
        "payments": payments,
        "q": q,
        "open_session": open_session,
    })
