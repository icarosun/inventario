from django.conf import settings
from django.db import models


class Department(models.Model):
    name = models.CharField("nome", max_length=150, unique=True)
    acronym = models.CharField("sigla", max_length=20, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "departamento"
        verbose_name_plural = "departamentos"

    def __str__(self):
        return f"{self.acronym} - {self.name}"


class InventoryItem(models.Model):
    class Category(models.TextChoices):
        TI = "TI", "TI"
        LOGISTICA = "LOGISTICA", "Logistica"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Ativo"
        MAINTENANCE = "MAINTENANCE", "Manutencao"
        STORED = "STORED", "Em estoque"
        RETIRED = "RETIRED", "Baixado"

    name = models.CharField("nome", max_length=150)
    category = models.CharField("categoria", max_length=20, choices=Category.choices)
    description = models.TextField("descricao", blank=True)
    department = models.ForeignKey(
        Department,
        verbose_name="departamento",
        related_name="items",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    responsible_person = models.CharField("responsavel", max_length=150, blank=True)
    immediate_supervisor = models.CharField("chefe imediato", max_length=150, blank=True)
    status = models.CharField(
        "status",
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    tombo_1 = models.CharField("tombo 1", max_length=80, blank=True)
    tombo_2 = models.CharField("tombo 2", max_length=80, blank=True)
    tombo_3 = models.CharField("tombo 3 ou numero de serie", max_length=80, blank=True)
    specs = models.JSONField("especificacoes", blank=True, default=dict)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="criado por",
        related_name="created_inventory_items",
        on_delete=models.PROTECT,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="atualizado por",
        related_name="updated_inventory_items",
        on_delete=models.PROTECT,
    )
    created_at = models.DateTimeField("criado em", auto_now_add=True)
    updated_at = models.DateTimeField("atualizado em", auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "item de inventario"
        verbose_name_plural = "itens de inventario"

    def __str__(self):
        return self.name


class InventoryImage(models.Model):
    item = models.ForeignKey(
        InventoryItem,
        verbose_name="item",
        related_name="images",
        on_delete=models.CASCADE,
    )
    image = models.ImageField("imagem", upload_to="inventory/items/%Y/%m/")
    caption = models.CharField("legenda", max_length=150, blank=True)
    uploaded_at = models.DateTimeField("enviado em", auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]
        verbose_name = "imagem do item"
        verbose_name_plural = "imagens dos itens"

    def __str__(self):
        return self.caption or f"Imagem de {self.item}"
