import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="InventoryItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=150, verbose_name="nome")),
                ("category", models.CharField(choices=[("TI", "TI"), ("LOGISTICA", "Logistica")], max_length=20, verbose_name="categoria")),
                ("description", models.TextField(blank=True, verbose_name="descricao")),
                ("location", models.CharField(blank=True, max_length=150, verbose_name="local")),
                ("responsible_person", models.CharField(blank=True, max_length=150, verbose_name="responsavel")),
                ("status", models.CharField(choices=[("ACTIVE", "Ativo"), ("MAINTENANCE", "Manutencao"), ("STORED", "Em estoque"), ("RETIRED", "Baixado")], default="ACTIVE", max_length=20, verbose_name="status")),
                ("tombo_1", models.CharField(blank=True, max_length=80, verbose_name="tombo 1")),
                ("tombo_2", models.CharField(blank=True, max_length=80, verbose_name="tombo 2")),
                ("tombo_3", models.CharField(blank=True, max_length=80, verbose_name="tombo 3")),
                ("specs", models.JSONField(blank=True, default=dict, verbose_name="especificacoes")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="criado em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="atualizado em")),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_inventory_items", to=settings.AUTH_USER_MODEL, verbose_name="criado por")),
                ("updated_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="updated_inventory_items", to=settings.AUTH_USER_MODEL, verbose_name="atualizado por")),
            ],
            options={
                "verbose_name": "item de inventario",
                "verbose_name_plural": "itens de inventario",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="InventoryImage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("image", models.ImageField(upload_to="inventory/items/%Y/%m/", verbose_name="imagem")),
                ("caption", models.CharField(blank=True, max_length=150, verbose_name="legenda")),
                ("uploaded_at", models.DateTimeField(auto_now_add=True, verbose_name="enviado em")),
                ("item", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="images", to="inventory.inventoryitem", verbose_name="item")),
            ],
            options={
                "verbose_name": "imagem do item",
                "verbose_name_plural": "imagens dos itens",
                "ordering": ["-uploaded_at"],
            },
        ),
    ]
