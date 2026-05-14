from django import forms
from .models import Table

INPUT_CLASS = "block w-full rounded-lg border border-slate-600 bg-slate-700 px-3 py-2 text-sm text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-400 focus:border-transparent"


class TableForm(forms.ModelForm):
    class Meta:
        model = Table
        fields = ["number", "capacity", "status"]
        widgets = {
            "number": forms.NumberInput(attrs={"class": INPUT_CLASS}),
            "capacity": forms.NumberInput(attrs={"class": INPUT_CLASS}),
            "status": forms.Select(attrs={"class": INPUT_CLASS}),
        }
