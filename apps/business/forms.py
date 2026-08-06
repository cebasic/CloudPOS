from django import forms

from .models import BusinessSettings

INPUT_CLASS = "input"


class BusinessSettingsForm(forms.ModelForm):
    class Meta:
        model = BusinessSettings
        fields = ["name", "tagline", "branch", "logo"]
        widgets = {
            "name": forms.TextInput(attrs={"class": INPUT_CLASS, "maxlength": 80}),
            "tagline": forms.TextInput(attrs={"class": INPUT_CLASS, "maxlength": 80}),
            "branch": forms.TextInput(attrs={"class": INPUT_CLASS, "maxlength": 80, "placeholder": "ej. Sucursal Centro"}),
            "logo": forms.ClearableFileInput(attrs={"accept": "image/*"}),
        }
