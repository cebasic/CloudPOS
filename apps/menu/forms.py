from django import forms
from .models import Category, MenuItem

INPUT_CLASS = "block w-full rounded-md border-0 py-2 px-3 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 sm:text-sm"


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
            "price": forms.NumberInput(attrs={"class": INPUT_CLASS, "step": "0.01"}),
            "available": forms.CheckboxInput(attrs={"class": "h-4 w-4 rounded border-gray-300 text-brand-600 focus:ring-brand-600"}),
            "image": forms.ClearableFileInput(attrs={"class": INPUT_CLASS}),
        }
