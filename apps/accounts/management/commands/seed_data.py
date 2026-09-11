from decimal import Decimal

from django.core.management.base import BaseCommand

from apps.accounts.models import User
from apps.tables.models import Table
from apps.menu.models import Category, MenuItem


class Command(BaseCommand):
    help = (
        "Seed the database with sample data for first-time setup. "
        "Skips automatically if the DB already looks initialized "
        "(unless --force is passed)."
    )

    @staticmethod
    def _get_or_create(model, defaults=None, **lookup):
        """get_or_create tolerante a duplicados ya existentes.

        El get_or_create normal revienta con MultipleObjectsReturned si la BD
        ya tiene filas repetidas (p. ej. dos categorías con el mismo nombre),
        lo que tumbaba el contenedor al re-ejecutar el seed. Aquí tomamos la
        primera coincidencia en vez de fallar.
        """
        obj = model.objects.filter(**lookup).first()
        if obj is not None:
            return obj, False
        return model.objects.create(**{**lookup, **(defaults or {})}), True

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help=(
                "Re-run seed even if the database already has data. "
                "Only recreates missing demo rows (get_or_create); "
                "does not overwrite existing users/menu/tables."
            ),
        )

    def handle(self, *args, **options):
        force = options["force"]
        already_initialized = (
            User.objects.filter(username="admin").exists()
            or Table.objects.exists()
            or Category.objects.exists()
            or MenuItem.objects.exists()
        )
        if already_initialized and not force:
            self.stdout.write(
                self.style.WARNING(
                    "Database already initialized — skipping seed_data "
                    "(pass --force to run anyway)."
                )
            )
            return

        self.stdout.write("Seeding database...")

        # Users
        admin, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "first_name": "Admin",
                "last_name": "Sistema",
                "role": "admin",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            admin.set_password("admin123")
            admin.save()
            self.stdout.write(self.style.SUCCESS("  Created admin user (admin / admin123)"))

        manager, created = User.objects.get_or_create(
            username="gerente",
            defaults={
                "first_name": "Carlos",
                "last_name": "Lopez",
                "role": "manager",
            },
        )
        if created:
            manager.set_password("gerente123")
            manager.save()
            self.stdout.write(self.style.SUCCESS("  Created manager user (gerente / gerente123)"))

        waiter, created = User.objects.get_or_create(
            username="mesero1",
            defaults={
                "first_name": "Maria",
                "last_name": "Garcia",
                "role": "waiter",
            },
        )
        if created:
            waiter.set_password("mesero123")
            waiter.save()
            self.stdout.write(self.style.SUCCESS("  Created waiter user (mesero1 / mesero123)"))

        waiter2, created = User.objects.get_or_create(
            username="mesero2",
            defaults={
                "first_name": "Juan",
                "last_name": "Martinez",
                "role": "waiter",
            },
        )
        if created:
            waiter2.set_password("mesero123")
            waiter2.save()
            self.stdout.write(self.style.SUCCESS("  Created waiter user (mesero2 / mesero123)"))

        kitchen_user, created = User.objects.get_or_create(
            username="cocina",
            defaults={
                "first_name": "Pedro",
                "last_name": "Sanchez",
                "role": "kitchen",
            },
        )
        if created:
            kitchen_user.set_password("cocina123")
            kitchen_user.save()
            self.stdout.write(self.style.SUCCESS("  Created kitchen user (cocina / cocina123)"))

        # Tables
        for i in range(1, 13):
            table, created = self._get_or_create(
                Table, {"capacity": 4 if i <= 8 else 6}, number=i,
            )
            if created:
                self.stdout.write(f"  Created Table {i}")

        # Menu Categories & Items
        entradas, _ = self._get_or_create(Category, {"order": 1}, name="Entradas")
        platos, _ = self._get_or_create(Category, {"order": 2}, name="Platos Fuertes")
        bebidas, _ = self._get_or_create(Category, {"order": 3}, name="Bebidas")
        postres, _ = self._get_or_create(Category, {"order": 4}, name="Postres")

        menu_items = [
            (entradas, "Nachos con Queso", "Totopos con queso gratinado, jalapeños y guacamole", Decimal("89.00")),
            (entradas, "Sopa de Tortilla", "Sopa tradicional con tiras de tortilla, aguacate y crema", Decimal("75.00")),
            (entradas, "Ensalada Caesar", "Lechuga romana, crutones, parmesano y aderezo caesar", Decimal("95.00")),
            (entradas, "Quesadillas", "Tortillas de harina con queso Oaxaca y champiñones", Decimal("85.00")),
            (platos, "Tacos al Pastor", "3 tacos con piña, cebolla y cilantro", Decimal("120.00")),
            (platos, "Enchiladas Verdes", "3 enchiladas con pollo, crema y queso", Decimal("135.00")),
            (platos, "Arrachera", "Corte de res a la parrilla con guarnicion", Decimal("250.00")),
            (platos, "Pollo a la Plancha", "Pechuga de pollo con ensalada y arroz", Decimal("155.00")),
            (platos, "Hamburguesa Clasica", "Carne angus, lechuga, tomate, cebolla y papas", Decimal("145.00")),
            (platos, "Salmon a la Parrilla", "Filete de salmon con vegetales y pure", Decimal("280.00")),
            (bebidas, "Agua Fresca", "Horchata, jamaica o limon (1 litro)", Decimal("45.00")),
            (bebidas, "Refresco", "Coca-Cola, Sprite o Fanta", Decimal("35.00")),
            (bebidas, "Cerveza Nacional", "Corona, Modelo o Victoria", Decimal("55.00")),
            (bebidas, "Limonada Mineral", "Agua mineral con limon y hierbabuena", Decimal("50.00")),
            (bebidas, "Cafe Americano", "Cafe de grano recien preparado", Decimal("40.00")),
            (postres, "Flan Napolitano", "Flan casero con caramelo", Decimal("65.00")),
            (postres, "Pastel de Chocolate", "Rebanada con helado de vainilla", Decimal("85.00")),
            (postres, "Churros con Chocolate", "4 churros con salsa de chocolate", Decimal("70.00")),
        ]

        for category, name, description, price in menu_items:
            _, created = self._get_or_create(
                MenuItem,
                {"category": category, "description": description, "price": price},
                name=name,
            )
            if created:
                self.stdout.write(f"  Created menu item: {name}")

        self.stdout.write(self.style.SUCCESS("\nSeed data loaded successfully!"))
        self.stdout.write(self.style.WARNING("\nLogin credentials:"))
        self.stdout.write("  admin    / admin123   (Administrador)")
        self.stdout.write("  gerente  / gerente123 (Gerente)")
        self.stdout.write("  mesero1  / mesero123  (Mesero)")
        self.stdout.write("  mesero2  / mesero123  (Mesero)")
        self.stdout.write("  cocina   / cocina123  (Cocina)")
