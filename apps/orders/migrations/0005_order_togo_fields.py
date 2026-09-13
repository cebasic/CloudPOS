from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0004_order_discount_by_order_discount_reason_and_more"),
        ("tables", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="order_type",
            field=models.CharField(
                choices=[
                    ("dine_in", "Mesa"),
                    ("pickup", "Para recoger"),
                    ("delivery", "Domicilio"),
                ],
                default="dine_in",
                max_length=20,
                verbose_name="Tipo",
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="customer_name",
            field=models.CharField(blank=True, max_length=120, verbose_name="Nombre del cliente"),
        ),
        migrations.AddField(
            model_name="order",
            name="customer_phone",
            field=models.CharField(blank=True, max_length=30, verbose_name="Teléfono"),
        ),
        migrations.AddField(
            model_name="order",
            name="delivery_address",
            field=models.TextField(blank=True, verbose_name="Dirección / referencia"),
        ),
        migrations.AddField(
            model_name="order",
            name="delivery_fee",
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                max_digits=10,
                verbose_name="Costo de envío",
            ),
        ),
        migrations.AlterField(
            model_name="order",
            name="table",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="orders",
                to="tables.table",
                verbose_name="Mesa",
            ),
        ),
    ]
