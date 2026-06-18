from .models import BusinessSettings


def business_settings(request):
    """Expone la identidad del negocio como ``business`` en todas las plantillas.

    Tolerante a fallos (p. ej. antes de migrar) para no romper el render.
    """
    try:
        return {"business": BusinessSettings.load()}
    except Exception:
        return {"business": None}
