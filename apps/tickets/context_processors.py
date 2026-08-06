from .models import TicketSettings


def ticket_settings(request):
    """Expone la configuración del ticket en todas las plantillas como ``ticket``.

    Es tolerante a fallos (p. ej. antes de migrar) para no romper el render.
    """
    try:
        return {"ticket": TicketSettings.load()}
    except Exception:
        return {"ticket": None}
