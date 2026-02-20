from django import forms
from .models import Table

INPUT_CLASS = "block w-full rounded-md border-0 py-2 px-3 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 sm:text-sm"


class TableForm(forms.ModelForm):
    class Meta:
        model = Table
        fields = ["number", "capacity", "status"]
        widgets = {
            "number": forms.NumberInput(attrs={"class": INPUT_CLASS}),
            "capacity": forms.NumberInput(attrs={"class": INPUT_CLASS}),
            "status": forms.Select(attrs={"class": INPUT_CLASS}),
        }
