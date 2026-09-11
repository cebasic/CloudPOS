from django.conf import settings
from django.db import models
from django.db.models import Sum


class CashSession(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Abierta"
        CLOSED = "closed", "Cerrada"

    opened_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="opened_sessions",
    )
    opened_at = models.DateTimeField(auto_now_add=True)
    initial_cash = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="closed_sessions",
    )
    closed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-opened_at"]
        verbose_name = "Sesión de Caja"
        verbose_name_plural = "Sesiones de Caja"

    def __str__(self):
        return f"Sesión #{self.pk} — {self.opened_by} ({self.get_status_display()})"

    def _payments_qs(self):
        from apps.orders.models import Payment
        qs = Payment.objects.filter(created_at__gte=self.opened_at)
        if self.closed_at:
            qs = qs.filter(created_at__lte=self.closed_at)
        return qs

    def _cash_revenue(self):
        """Net cash that came into the register from order payments."""
        from apps.orders.models import Payment
        qs = self._payments_qs()
        pure_cash = qs.filter(method="cash").aggregate(t=Sum("total"))["t"] or 0
        mixed_cash = qs.filter(method="mixed").aggregate(t=Sum("cash_amount"))["t"] or 0
        return pure_cash + mixed_cash

    def _card_revenue(self):
        from apps.orders.models import Payment
        qs = self._payments_qs()
        pure_card = qs.filter(method="card").aggregate(t=Sum("total"))["t"] or 0
        mixed_card = qs.filter(method="mixed").aggregate(t=Sum("card_amount"))["t"] or 0
        return pure_card + mixed_card

    def cash_sales(self):
        return self._cash_revenue()

    def card_sales(self):
        return self._card_revenue()

    def total_sales(self):
        return self._payments_qs().aggregate(t=Sum("total"))["t"] or 0

    def order_count(self):
        return self._payments_qs().count()

    def change_given(self):
        return self._payments_qs().aggregate(t=Sum("change_due"))["t"] or 0

    def total_tips(self):
        return self._payments_qs().aggregate(t=Sum("tip"))["t"] or 0

    def total_expenses(self):
        return self.expenses.aggregate(t=Sum("amount"))["t"] or 0

    def expected_in_drawer(self):
        """Fondo inicial + ventas en efectivo − gastos del turno."""
        return self.initial_cash + self.cash_sales() - self.total_expenses()

    def net_revenue(self):
        return self.total_sales() - self.total_expenses()


class Expense(models.Model):
    class Category(models.TextChoices):
        SUPPLIES = "supplies", "Insumos"
        UTILITIES = "utilities", "Servicios"
        STAFF = "staff", "Personal"
        OTHER = "other", "Otro"

    session = models.ForeignKey(
        CashSession, on_delete=models.CASCADE,
        related_name="expenses", null=True, blank=True,
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.OTHER)
    description = models.CharField(max_length=200)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="expenses",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Gasto"
        verbose_name_plural = "Gastos"

    def __str__(self):
        return f"{self.get_category_display()} — ${self.amount} ({self.description[:40]})"


class CashCut(models.Model):
    class CutType(models.TextChoices):
        PARTIAL = "partial", "Corte Parcial"
        FINAL = "final", "Corte Final"

    session = models.ForeignKey(CashSession, on_delete=models.CASCADE, related_name="cuts")
    cut_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="cash_cuts",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    cut_type = models.CharField(max_length=10, choices=CutType.choices, default=CutType.PARTIAL)

    # Snapshot captured at cut time
    initial_cash = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cash_sales = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    card_sales = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    change_given = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    order_count = models.PositiveIntegerField(default=0)
    total_tips = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_expenses = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Manual reconciliation
    cash_counted = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cash_expected = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cash_difference = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Corte de Caja"
        verbose_name_plural = "Cortes de Caja"

    def __str__(self):
        return f"Corte #{self.pk} ({self.get_cut_type_display()}) — {self.created_at:%d/%m/%Y %H:%M}"

    @property
    def total_sales(self):
        return self.cash_sales + self.card_sales

    @property
    def net_revenue(self):
        return self.total_sales - self.total_expenses
