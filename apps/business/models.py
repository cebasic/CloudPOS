from django.db import models
from django.conf import settings


class BusinessSettings(models.Model):
    """Identidad del negocio (singleton) usada en la marca de la app:
    avatar de la barra lateral, nombre y lema.

    Siempre existe una sola fila (pk=1). Usa ``BusinessSettings.load()``.
    """

    name = models.CharField("Nombre del restaurant", max_length=80, default="Cocos Barrancos")
    tagline = models.CharField("Lema", max_length=80, blank=True, default="Casa · Mar · Brasa")
    branch = models.CharField("Sucursal", max_length=80, blank=True)
    logo = models.ImageField("Logo", upload_to="business/", blank=True, null=True)

    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )

    class Meta:
        verbose_name = "Configuración del negocio"
        verbose_name_plural = "Configuración del negocio"

    def __str__(self):
        return f"Negocio · {self.name}"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @property
    def tagline_parts(self):
        """Lema dividido por '·' para el hero del login (cada parte en su línea)."""
        if not self.tagline:
            return []
        return [p.strip() for p in self.tagline.split("·") if p.strip()]
