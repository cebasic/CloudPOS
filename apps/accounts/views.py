from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from .decorators import role_required, get_home_url
from .forms import LoginForm, UserForm
from .models import User


def login_view(request):
    if request.user.is_authenticated:
        return redirect(get_home_url(request.user))
    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)
        next_url = request.GET.get("next")
        return redirect(next_url if next_url else get_home_url(user))
    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("accounts:login")


@login_required
@role_required("admin")
def user_list(request):
    users = User.objects.all()
    return render(request, "accounts/user_list.html", {"users": users})


@login_required
@role_required("admin")
def user_create(request):
    form = UserForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save(commit=False)
        password = form.cleaned_data.get("password")
        if not password:
            messages.error(request, "La contrasena es obligatoria para nuevos usuarios.")
            return render(request, "accounts/user_form.html", {"form": form, "title": "Nuevo Usuario"})
        user.set_password(password)
        user.save()
        messages.success(request, "Usuario creado exitosamente.")
        return redirect("accounts:user_list")
    return render(request, "accounts/user_form.html", {"form": form, "title": "Nuevo Usuario"})


@login_required
@role_required("admin")
def user_edit(request, pk):
    user = get_object_or_404(User, pk=pk)
    form = UserForm(request.POST or None, instance=user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Usuario actualizado exitosamente.")
        return redirect("accounts:user_list")
    return render(request, "accounts/user_form.html", {"form": form, "title": f"Editar: {user.username}"})


@login_required
@role_required("admin")
def user_toggle_active(request, pk):
    user = get_object_or_404(User, pk=pk)
    user.is_active = not user.is_active
    user.save(update_fields=["is_active"])
    status = "activado" if user.is_active else "desactivado"
    messages.success(request, f"Usuario {user.username} {status}.")
    return redirect("accounts:user_list")
