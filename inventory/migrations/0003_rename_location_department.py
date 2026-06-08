from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0002_inventoryitem_immediate_supervisor"),
    ]

    operations = [
        migrations.RenameField(
            model_name="inventoryitem",
            old_name="location",
            new_name="department",
        ),
        migrations.AlterField(
            model_name="inventoryitem",
            name="department",
            field=models.CharField(blank=True, max_length=150, verbose_name="departamento"),
        ),
    ]
