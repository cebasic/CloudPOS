from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def get_home_url(user):
    """Return the default landing URL based on the user's role."""
    role = getattr(user, "role", None)
    if role == "kitchen":
        return "kitchen:display"
    if role == "cashier":
        return "cashier:dashboard"
    return "orders:dashboard"


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if request.user.is_authenticated and request.user.role in roles:
                return view_func(request, *args, **kwargs)
            messages.error(request, "No tienes permiso para acceder a esta seccion.")
            return redirect(get_home_url(request.user))
        return _wrapped
    return decorator
