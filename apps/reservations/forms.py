from django import forms
from .models import Reservation

_INPUT = "input"


class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ["customer_name", "customer_phone", "date", "time", "party_size", "table", "notes"]
        widgets = {
            "customer_name": forms.TextInput(attrs={"class": _INPUT, "placeholder": "Nombre del cliente"}),
            "customer_phone": forms.TextInput(attrs={"class": _INPUT, "placeholder": "10 dígitos"}),
            "date": forms.DateInput(attrs={"class": _INPUT, "type": "date"}),
            "time": forms.TimeInput(attrs={"class": _INPUT, "type": "time"}),
            "party_size": forms.NumberInput(attrs={"class": _INPUT, "min": "1", "max": "50"}),
            "table": forms.Select(attrs={"class": _INPUT}),
            "notes": forms.Textarea(attrs={"class": _INPUT, "rows": 2, "placeholder": "Alergias, ocasión especial..."}),
        }
