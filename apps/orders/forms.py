from django import forms
from .models import Order, OrderItem, Payment
from apps.tables.models import Table
from apps.menu.models import MenuItem

INPUT_CLASS = "input"


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


class TakeoutOrderForm(forms.ModelForm):
    """Alta rápida desde caja: recoger o domicilio."""

    class Meta:
        model = Order
        fields = [
            "order_type",
            "customer_name",
            "customer_phone",
            "notes",
            "delivery_address",
            "delivery_fee",
        ]
        widgets = {
            "order_type": forms.RadioSelect,
            "customer_name": forms.TextInput(attrs={
                "class": INPUT_CLASS, "placeholder": "Nombre del cliente", "autocomplete": "name",
            }),
            "customer_phone": forms.TextInput(attrs={
                "class": INPUT_CLASS, "placeholder": "Teléfono", "autocomplete": "tel",
            }),
            "notes": forms.Textarea(attrs={
                "class": INPUT_CLASS, "rows": 2, "placeholder": "Notas para cocina o del pedido...",
            }),
            "delivery_address": forms.Textarea(attrs={
                "class": INPUT_CLASS, "rows": 2, "placeholder": "Calle, colonia, referencias...",
            }),
            "delivery_fee": forms.NumberInput(attrs={
                "class": INPUT_CLASS, "step": "0.01", "min": "0", "placeholder": "0.00",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["order_type"].choices = [
            (Order.OrderType.PICKUP, "Para recoger"),
            (Order.OrderType.DELIVERY, "Domicilio"),
        ]
        self.fields["customer_name"].required = True
        self.fields["customer_phone"].required = False
        self.fields["notes"].required = False
        self.fields["delivery_address"].required = False
        self.fields["delivery_fee"].required = False
        self.fields["delivery_fee"].localize = False
        self.fields["delivery_fee"].widget.is_localized = False
        if not self.is_bound and not self.initial.get("order_type"):
            self.initial["order_type"] = Order.OrderType.PICKUP
            self.initial["delivery_fee"] = 0

    def clean_order_type(self):
        value = self.cleaned_data["order_type"]
        if value not in (Order.OrderType.PICKUP, Order.OrderType.DELIVERY):
            raise forms.ValidationError("Selecciona Para recoger o Domicilio.")
        return value

    def clean(self):
        cleaned = super().clean()
        order_type = cleaned.get("order_type")
        if order_type == Order.OrderType.DELIVERY:
            address = (cleaned.get("delivery_address") or "").strip()
            if not address:
                self.add_error("delivery_address", "La dirección es obligatoria para domicilio.")
            fee = cleaned.get("delivery_fee")
            if fee is None:
                cleaned["delivery_fee"] = 0
            elif fee < 0:
                self.add_error("delivery_fee", "El costo de envío no puede ser negativo.")
        else:
            cleaned["delivery_address"] = ""
            cleaned["delivery_fee"] = 0
        return cleaned


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
        tip = cleaned.get("tip") or 0
        due_total = (self.order_total or 0) + tip
        if method == "cash":
            if not amount:
                self.add_error("amount_received", "Ingresa el monto recibido para pago en efectivo.")
            elif self.order_total is not None and amount < due_total:
                self.add_error(
                    "amount_received",
                    f"El monto debe ser al menos ${due_total} (total + propina).",
                )
        if method == "mixed":
            cash = cleaned.get("cash_amount") or 0
            card = cleaned.get("card_amount") or 0
            if not cash and not card:
                self.add_error("cash_amount", "Ingresa los montos de efectivo y tarjeta.")
            elif self.order_total is not None and (cash + card) < due_total:
                self.add_error(
                    "cash_amount",
                    f"La suma debe ser al menos ${due_total} (total + propina).",
                )
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
