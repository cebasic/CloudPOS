from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Administrador"
        MANAGER = "manager", "Gerente"
        WAITER = "waiter", "Mesero"
        KITCHEN = "kitchen", "Cocina"
        CASHIER = "cashier", "Cajero"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.WAITER)

    class Meta:
        ordering = ["username"]

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"
