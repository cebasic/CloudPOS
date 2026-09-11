from django import forms
from .models import Category, MenuItem

INPUT_CLASS = "input"


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "description", "order"]
        widgets = {
            "name": forms.TextInput(attrs={"class": INPUT_CLASS}),
            "description": forms.Textarea(attrs={"class": INPUT_CLASS, "rows": 3}),
            "order": forms.NumberInput(attrs={"class": INPUT_CLASS}),
        }


class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = ["category", "name", "description", "price", "available", "image"]
        widgets = {
            "category": forms.Select(attrs={"class": INPUT_CLASS}),
            "name": forms.TextInput(attrs={"class": INPUT_CLASS}),
            "description": forms.Textarea(attrs={"class": INPUT_CLASS, "rows": 3}),
            "price": forms.NumberInput(attrs={
                "class": INPUT_CLASS, "step": "0.01", "min": "0", "placeholder": "0.00",
            }),
            "available": forms.CheckboxInput(attrs={"class": "h-4 w-4 rounded border-slate-500 bg-slate-700 text-brand-500 focus:ring-brand-500"}),
            "image": forms.ClearableFileInput(attrs={"class": INPUT_CLASS}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # input[type=number] needs a dot decimal; Spanish localization would
        # render "120,00" and the browser shows 0 / empty on edit.
        self.fields["price"].localize = False
        self.fields["price"].widget.is_localized = False
