from django import forms
from .models import Reservation

_INPUT = (
    "block w-full rounded-lg border border-slate-600 bg-slate-700 px-3 py-2 "
    "text-sm text-white placeholder-slate-400 focus:outline-none "
    "focus:ring-2 focus:ring-brand-400 focus:border-transparent"
)


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
