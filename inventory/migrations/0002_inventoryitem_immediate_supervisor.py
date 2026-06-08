from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="inventoryitem",
            name="immediate_supervisor",
            field=models.CharField(blank=True, max_length=150, verbose_name="chefe imediato"),
        ),
    ]
