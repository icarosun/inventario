from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0007_inventoryaudit_inventoryitemmovement_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="inventoryitemmovement",
            old_name="caution_document",
            new_name="delivery_caution_document",
        ),
        migrations.AlterField(
            model_name="inventoryitemmovement",
            name="delivery_caution_document",
            field=models.FileField(upload_to="inventory/movements/cautions/%Y/%m/", verbose_name="cautela de entrega"),
        ),
        migrations.AddField(
            model_name="inventoryitemmovement",
            name="return_caution_document",
            field=models.FileField(blank=True, upload_to="inventory/movements/cautions/%Y/%m/", verbose_name="cautela de devolucao"),
        ),
    ]
