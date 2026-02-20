from django import forms
from .models import Order, OrderItem, Payment
from apps.tables.models import Table
from apps.menu.models import MenuItem

INPUT_CLASS = "block w-full rounded-md border-0 py-2 px-3 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 sm:text-sm"


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
            "class": INPUT_CLASS,
            "step": "0.01",
            "min": "0",
            "placeholder": "Monto recibido",
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
        return cleaned
