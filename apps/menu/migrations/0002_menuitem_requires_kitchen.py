from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("menu", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="menuitem",
            name="requires_kitchen",
            field=models.BooleanField(
                default=True,
                help_text="Desactiva para refrescos, té embotellado, etc. que sirve el mesero.",
                verbose_name="Enviar a cocina",
            ),
        ),
    ]
