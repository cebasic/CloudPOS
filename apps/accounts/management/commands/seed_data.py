from decimal import Decimal

from django.core.management.base import BaseCommand

from apps.accounts.models import User
from apps.tables.models import Table
from apps.menu.models import Category, MenuItem


class Command(BaseCommand):
    help = "Seed the database with sample data for development"

    def handle(self, *args, **options):
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
            table, created = Table.objects.get_or_create(
                number=i,
                defaults={"capacity": 4 if i <= 8 else 6},
            )
            if created:
                self.stdout.write(f"  Created Table {i}")

        # Menu Categories & Items
        entradas, _ = Category.objects.get_or_create(name="Entradas", defaults={"order": 1})
        platos, _ = Category.objects.get_or_create(name="Platos Fuertes", defaults={"order": 2})
        bebidas, _ = Category.objects.get_or_create(name="Bebidas", defaults={"order": 3})
        postres, _ = Category.objects.get_or_create(name="Postres", defaults={"order": 4})

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
            _, created = MenuItem.objects.get_or_create(
                name=name,
                defaults={
                    "category": category,
                    "description": description,
                    "price": price,
                },
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
