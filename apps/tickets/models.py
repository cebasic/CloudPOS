from django.db import models
from django.conf import settings


class TicketSettings(models.Model):
    """Configuración única (singleton) del ticket/recibo del negocio.

    Siempre existe una sola fila (pk=1). Usa ``TicketSettings.load()`` para
    obtenerla, creándola con los valores por defecto la primera vez.
    """

    class Paper(models.TextChoices):
        MM58 = "58", "58 mm (angosto)"
        MM80 = "80", "80 mm (estándar)"

    # Identidad del negocio
    business_name = models.CharField("Nombre del negocio", max_length=80, default="Cocos Barrancos")
    tagline = models.CharField("Lema", max_length=80, blank=True, default="Casa · Mar · Brasa")
    logo = models.ImageField("Logo", upload_to="ticket/", blank=True, null=True)

    # Datos fiscales / contacto
    address = models.CharField("Dirección", max_length=160, blank=True)
    phone = models.CharField("Teléfono", max_length=40, blank=True)
    tax_id = models.CharField("RFC", max_length=40, blank=True)
    billing_url = models.CharField("URL de facturación", max_length=300, blank=True)

    # Mensajes
    header_note = models.CharField("Nota de encabezado", max_length=120, blank=True)
    footer_message = models.CharField(
        "Mensaje de pie", max_length=160, blank=True, default="¡Gracias por su visita!"
    )

    # Apariencia
    accent_color = models.CharField("Color de acento", max_length=7, default="#C8553D")
    paper_width = models.CharField("Ancho de papel", max_length=2, choices=Paper.choices, default=Paper.MM80)

    # Visibilidad de secciones
    show_logo = models.BooleanField("Mostrar logo", default=True)
    show_address = models.BooleanField("Mostrar dirección", default=True)
    show_phone = models.BooleanField("Mostrar teléfono", default=True)
    show_tax_id = models.BooleanField("Mostrar RFC", default=False)
    show_qr = models.BooleanField("Mostrar QR de facturación", default=True)
    show_table = models.BooleanField("Mostrar mesa", default=True)
    show_cashier = models.BooleanField("Mostrar cajero", default=True)
    show_datetime = models.BooleanField("Mostrar fecha y hora", default=True)

    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )

    class Meta:
        verbose_name = "Configuración del ticket"
        verbose_name_plural = "Configuración del ticket"

    def __str__(self):
        return f"Ticket · {self.business_name}"

    def save(self, *args, **kwargs):
        # Forzar singleton: siempre pk=1.
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
