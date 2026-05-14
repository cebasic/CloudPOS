from django.conf import settings
from django.db import models
from django.utils import timezone


class Reservation(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendiente"
        CONFIRMED = "confirmed", "Confirmada"
        SEATED = "seated", "Sentada"
        CANCELLED = "cancelled", "Cancelada"
        NO_SHOW = "no_show", "No se presentó"

    customer_name = models.CharField(max_length=100, verbose_name="Nombre")
    customer_phone = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    date = models.DateField(verbose_name="Fecha")
    time = models.TimeField(verbose_name="Hora")
    party_size = models.PositiveIntegerField(verbose_name="Personas")
    table = models.ForeignKey(
        "tables.Table", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="reservations",
        verbose_name="Mesa asignada",
    )
    status = models.CharField(
        max_length=15, choices=Status.choices, default=Status.PENDING,
    )
    notes = models.TextField(blank=True, verbose_name="Notas")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="reservations",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date", "time"]
        verbose_name = "Reservación"
        verbose_name_plural = "Reservaciones"

    def __str__(self):
        return f"{self.customer_name} — {self.date} {self.time:%H:%M} ({self.party_size}p)"

    @property
    def is_today(self):
        return self.date == timezone.localdate()

    @property
    def is_active(self):
        return self.status in (self.Status.PENDING, self.Status.CONFIRMED)
