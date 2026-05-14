from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import User


_INPUT = "block w-full rounded-lg border border-slate-600 bg-slate-700 px-3 py-2 text-sm text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-400 focus:border-transparent"


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={"class": _INPUT, "placeholder": "Usuario"})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": _INPUT, "placeholder": "Contraseña"})
    )


class UserForm(forms.ModelForm):
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={"class": _INPUT, "placeholder": "Dejar vacío para no cambiar"}),
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "role", "is_active"]
        widgets = {
            "username": forms.TextInput(attrs={"class": _INPUT}),
            "first_name": forms.TextInput(attrs={"class": _INPUT}),
            "last_name": forms.TextInput(attrs={"class": _INPUT}),
            "email": forms.EmailInput(attrs={"class": _INPUT}),
            "role": forms.Select(attrs={"class": _INPUT}),
            "is_active": forms.CheckboxInput(attrs={"class": "h-4 w-4 rounded border-slate-500 bg-slate-700 text-brand-500 focus:ring-brand-500"}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password")
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user
