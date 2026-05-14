from django import forms
from .models import Category, MenuItem

INPUT_CLASS = "block w-full rounded-lg border border-slate-600 bg-slate-700 px-3 py-2 text-sm text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-400 focus:border-transparent"


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
            "available": forms.CheckboxInput(attrs={"class": "h-4 w-4 rounded border-slate-500 bg-slate-700 text-brand-500 focus:ring-brand-500"}),
            "image": forms.ClearableFileInput(attrs={"class": INPUT_CLASS}),
        }
