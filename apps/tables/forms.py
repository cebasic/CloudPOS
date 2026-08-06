from django import forms
from .models import Table

INPUT_CLASS = "input"


class TableForm(forms.ModelForm):
    class Meta:
        model = Table
        fields = ["number", "capacity", "status"]
        widgets = {
            "number": forms.NumberInput(attrs={"class": INPUT_CLASS}),
            "capacity": forms.NumberInput(attrs={"class": INPUT_CLASS}),
            "status": forms.Select(attrs={"class": INPUT_CLASS}),
        }
