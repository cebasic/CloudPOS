from django import forms

from .models import TicketSettings

INPUT_CLASS = "input"


class TicketSettingsForm(forms.ModelForm):
    class Meta:
        model = TicketSettings
        fields = [
            "business_name", "tagline", "logo",
            "address", "phone", "tax_id", "billing_url",
            "header_note", "footer_message",
            "accent_color", "paper_width",
            "show_logo", "show_address", "show_phone", "show_tax_id", "show_qr",
            "show_table", "show_cashier", "show_datetime",
        ]
        widgets = {
            "business_name": forms.TextInput(attrs={"class": INPUT_CLASS, "maxlength": 80}),
            "tagline": forms.TextInput(attrs={"class": INPUT_CLASS, "maxlength": 80}),
            "logo": forms.ClearableFileInput(attrs={"accept": "image/*"}),
            "address": forms.TextInput(attrs={"class": INPUT_CLASS, "maxlength": 160}),
            "phone": forms.TextInput(attrs={"class": INPUT_CLASS, "maxlength": 40}),
            "tax_id": forms.TextInput(attrs={"class": INPUT_CLASS, "maxlength": 40}),
            "billing_url": forms.TextInput(attrs={"class": INPUT_CLASS, "maxlength": 300, "placeholder": "https://factura.minegocio.com"}),
            "header_note": forms.TextInput(attrs={"class": INPUT_CLASS, "maxlength": 120}),
            "footer_message": forms.TextInput(attrs={"class": INPUT_CLASS, "maxlength": 160}),
            "paper_width": forms.Select(attrs={"class": "select"}),
            "accent_color": forms.TextInput(attrs={"type": "color", "class": "color-input"}),
        }
