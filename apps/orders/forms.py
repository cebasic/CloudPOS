from django import forms
from .models import Order, OrderItem, Payment
from apps.tables.models import Table
from apps.menu.models import MenuItem

INPUT_CLASS = "block w-full rounded-lg border border-slate-600 bg-slate-700 px-3 py-2 text-sm text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-400 focus:border-transparent"


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["table", "notes"]
        widgets = {
            "table": forms.Select(attrs={"class": INPUT_CLASS}),
            "notes": forms.Textarea(attrs={"class": INPUT_CLASS, "rows": 2, "placeholder": "Notas generales..."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields["table"].queryset = Table.objects.filter(status="available")
        else:
            self.fields["table"].queryset = Table.objects.all()


class OrderItemForm(forms.Form):
    menu_item = forms.ModelChoiceField(
        queryset=MenuItem.objects.filter(available=True),
        widget=forms.Select(attrs={"class": INPUT_CLASS}),
    )
    quantity = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={"class": INPUT_CLASS, "min": "1"}),
    )
    notes = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": INPUT_CLASS, "placeholder": "Sin cebolla, extra queso..."}),
    )


class PaymentForm(forms.Form):
    method = forms.ChoiceField(
        choices=Payment.Method.choices,
        widget=forms.RadioSelect(attrs={"class": "h-4 w-4 text-brand-600 focus:ring-brand-600"}),
    )
    amount_received = forms.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            "class": INPUT_CLASS, "step": "0.01", "min": "0", "placeholder": "Monto recibido",
        }),
    )
    tip = forms.DecimalField(
        required=False,
        min_value=0,
        max_digits=10,
        decimal_places=2,
        initial=0,
        widget=forms.NumberInput(attrs={
            "class": INPUT_CLASS, "step": "0.01", "min": "0", "placeholder": "0.00",
        }),
    )
    cash_amount = forms.DecimalField(
        required=False,
        min_value=0,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            "class": INPUT_CLASS, "step": "0.01", "min": "0", "placeholder": "Monto en efectivo",
        }),
    )
    card_amount = forms.DecimalField(
        required=False,
        min_value=0,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            "class": INPUT_CLASS, "step": "0.01", "min": "0", "placeholder": "Monto en tarjeta",
        }),
    )

    def __init__(self, *args, order_total=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.order_total = order_total

    def clean(self):
        cleaned = super().clean()
        method = cleaned.get("method")
        amount = cleaned.get("amount_received")
        if method == "cash":
            if not amount:
                self.add_error("amount_received", "Ingresa el monto recibido para pago en efectivo.")
            elif self.order_total and amount < self.order_total:
                self.add_error("amount_received", f"El monto debe ser al menos ${self.order_total}.")
        if method == "mixed":
            cash = cleaned.get("cash_amount") or 0
            card = cleaned.get("card_amount") or 0
            if not cash and not card:
                self.add_error("cash_amount", "Ingresa los montos de efectivo y tarjeta.")
            elif self.order_total and (cash + card) < self.order_total:
                self.add_error("cash_amount", f"La suma debe ser al menos ${self.order_total}.")
        return cleaned


class DiscountForm(forms.Form):
    discount_type = forms.ChoiceField(
        choices=[("percentage", "Porcentaje %"), ("fixed", "Monto fijo $")],
        widget=forms.RadioSelect(attrs={"class": "h-4 w-4 text-brand-600 focus:ring-brand-600"}),
    )
    discount_value = forms.DecimalField(
        min_value=0,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            "class": INPUT_CLASS, "step": "0.01", "min": "0", "placeholder": "0.00",
        }),
    )
    discount_reason = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={"class": INPUT_CLASS, "placeholder": "Motivo del descuento o cortesía"}),
    )
