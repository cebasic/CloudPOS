from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages

from apps.accounts.decorators import role_required
from .models import CashSession, CashCut, Expense
from .forms import OpenSessionForm, CashCutForm, ExpenseForm

_ROLES = ("admin", "manager", "cashier")


def _open_session():
    return CashSession.objects.filter(status="open").first()


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
    return render(request, "cashier/dashboard.html", {
        "session": session,
        "recent_cuts": recent_cuts,
        "recent_sessions": recent_sessions,
        "expenses": expenses,
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
