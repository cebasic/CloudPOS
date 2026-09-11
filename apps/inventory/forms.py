from decimal import Decimal

from django import forms
from django.forms import inlineformset_factory

from apps.menu.models import MenuItem

from .models import RecipeLine, StockItem

_INPUT = "input"


class StockItemForm(forms.ModelForm):
    class Meta:
        model = StockItem
        fields = [
            "name", "item_type", "unit", "par_level", "reorder_qty",
            "menu_item", "is_active", "notes",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": _INPUT}),
            "item_type": forms.Select(attrs={"class": _INPUT}),
            "unit": forms.Select(attrs={"class": _INPUT}),
            "par_level": forms.NumberInput(attrs={"class": _INPUT, "step": "0.001", "min": "0"}),
            "reorder_qty": forms.NumberInput(attrs={"class": _INPUT, "step": "0.001", "min": "0"}),
            "menu_item": forms.Select(attrs={"class": _INPUT}),
            "is_active": forms.CheckboxInput(attrs={"class": "h-4 w-4"}),
            "notes": forms.TextInput(attrs={"class": _INPUT}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["par_level"].localize = False
        self.fields["reorder_qty"].localize = False
        linked_ids = list(
            StockItem.objects.exclude(menu_item=None).values_list("menu_item_id", flat=True)
        )
        if self.instance and self.instance.menu_item_id:
            linked_ids = [i for i in linked_ids if i != self.instance.menu_item_id]
        self.fields["menu_item"].queryset = MenuItem.objects.exclude(pk__in=linked_ids).order_by("name")
        self.fields["menu_item"].required = False
        self.fields["menu_item"].help_text = (
            "Opcional: para bebidas/productos que se descuentan 1:1 al vender."
        )


class PurchaseForm(forms.Form):
    quantity = forms.DecimalField(
        min_value=Decimal("0.001"),
        max_digits=12,
        decimal_places=3,
        label="Cantidad",
        widget=forms.NumberInput(attrs={"class": _INPUT, "step": "0.001", "min": "0.001"}),
    )
    note = forms.CharField(
        required=False,
        max_length=240,
        label="Nota",
        widget=forms.TextInput(attrs={"class": _INPUT, "placeholder": "Proveedor, factura…"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["quantity"].localize = False


class ManualAdjustForm(forms.Form):
    quantity_delta = forms.DecimalField(
        max_digits=12,
        decimal_places=3,
        label="Ajuste (+ entrada / − salida)",
        widget=forms.NumberInput(attrs={"class": _INPUT, "step": "0.001"}),
    )
    note = forms.CharField(
        required=False,
        max_length=240,
        widget=forms.TextInput(attrs={"class": _INPUT, "placeholder": "Motivo"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["quantity_delta"].localize = False

    def clean_quantity_delta(self):
        val = self.cleaned_data["quantity_delta"]
        if val == 0:
            raise forms.ValidationError("El ajuste no puede ser 0.")
        return val


class WasteForm(forms.Form):
    quantity = forms.DecimalField(
        min_value=Decimal("0.001"),
        max_digits=12,
        decimal_places=3,
        label="Cantidad merma",
        widget=forms.NumberInput(attrs={"class": _INPUT, "step": "0.001", "min": "0.001"}),
    )
    note = forms.CharField(
        required=False,
        max_length=240,
        widget=forms.TextInput(attrs={"class": _INPUT, "placeholder": "Motivo de merma"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["quantity"].localize = False


class RecipeLineForm(forms.ModelForm):
    class Meta:
        model = RecipeLine
        fields = ["stock_item", "quantity"]
        widgets = {
            "stock_item": forms.Select(attrs={"class": _INPUT}),
            "quantity": forms.NumberInput(attrs={"class": _INPUT, "step": "0.001", "min": "0.001"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["quantity"].localize = False
        self.fields["stock_item"].queryset = StockItem.objects.filter(is_active=True).order_by("name")


RecipeLineFormSet = inlineformset_factory(
    MenuItem,
    RecipeLine,
    form=RecipeLineForm,
    extra=3,
    can_delete=True,
)


class StockCountForm(forms.Form):
    """Dynamic count: fields added in the view per stock item."""

    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": _INPUT, "rows": 2, "placeholder": "Notas del conteo"}),
    )
