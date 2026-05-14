from django import forms
from .models import CashCut, Expense

_INPUT = (
    "block w-full rounded-lg border border-slate-600 bg-slate-700 px-3 py-2 "
    "text-sm text-white placeholder-slate-400 focus:outline-none "
    "focus:ring-2 focus:ring-brand-400 focus:border-transparent"
)


class OpenSessionForm(forms.Form):
    initial_cash = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        label="Fondo Inicial (caja chica)",
        widget=forms.NumberInput(attrs={
            "class": _INPUT,
            "step": "0.01",
            "min": "0",
            "placeholder": "0.00",
            "autofocus": True,
        }),
    )
    notes = forms.CharField(
        required=False,
        label="Notas de apertura",
        widget=forms.Textarea(attrs={
            "class": _INPUT,
            "rows": 2,
            "placeholder": "Observaciones opcionales...",
        }),
    )


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ["category", "amount", "description"]
        widgets = {
            "category": forms.Select(attrs={"class": _INPUT}),
            "amount": forms.NumberInput(attrs={
                "class": _INPUT, "step": "0.01", "min": "0.01", "placeholder": "0.00",
            }),
            "description": forms.TextInput(attrs={
                "class": _INPUT, "placeholder": "Descripción del gasto",
            }),
        }


class CashCutForm(forms.Form):
    cut_type = forms.ChoiceField(
        choices=CashCut.CutType.choices,
        label="Tipo de Corte",
        initial=CashCut.CutType.PARTIAL,
    )
    cash_counted = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        label="Efectivo Contado en Caja",
        widget=forms.NumberInput(attrs={
            "class": _INPUT,
            "step": "0.01",
            "min": "0",
            "placeholder": "0.00",
            "autofocus": True,
            "id": "cash-counted-input",
        }),
    )
    notes = forms.CharField(
        required=False,
        label="Notas del corte",
        widget=forms.Textarea(attrs={
            "class": _INPUT,
            "rows": 2,
            "placeholder": "Observaciones del corte...",
        }),
    )
