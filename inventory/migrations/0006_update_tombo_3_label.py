from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0005_department_acronym"),
    ]

    operations = [
        migrations.AlterField(
            model_name="inventoryitem",
            name="tombo_3",
            field=models.CharField(blank=True, max_length=80, verbose_name="tombo 3 ou numero de serie"),
        ),
    ]
