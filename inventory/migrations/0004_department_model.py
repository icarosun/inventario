import django.db.models.deletion
from django.db import migrations, models


def copy_department_names(apps, schema_editor):
    Department = apps.get_model("inventory", "Department")
    InventoryItem = apps.get_model("inventory", "InventoryItem")

    for item in InventoryItem.objects.exclude(department=""):
        name = item.department.strip()
        if not name:
            continue
        department, _ = Department.objects.get_or_create(name=name)
        item.department_ref = department
        item.save(update_fields=["department_ref"])


def copy_department_refs_back(apps, schema_editor):
    InventoryItem = apps.get_model("inventory", "InventoryItem")

    for item in InventoryItem.objects.select_related("department_ref"):
        item.department = item.department_ref.name if item.department_ref else ""
        item.save(update_fields=["department"])


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0003_rename_location_department"),
    ]

    operations = [
        migrations.CreateModel(
            name="Department",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=150, unique=True, verbose_name="nome")),
            ],
            options={
                "verbose_name": "departamento",
                "verbose_name_plural": "departamentos",
                "ordering": ["name"],
            },
        ),
        migrations.AddField(
            model_name="inventoryitem",
            name="department_ref",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="items",
                to="inventory.department",
                verbose_name="departamento",
            ),
        ),
        migrations.RunPython(copy_department_names, copy_department_refs_back),
        migrations.RemoveField(
            model_name="inventoryitem",
            name="department",
        ),
        migrations.RenameField(
            model_name="inventoryitem",
            old_name="department_ref",
            new_name="department",
        ),
    ]
