from django.conf import settings
from django.db import models
from django.utils import timezone


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


class InventoryAudit(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Aberta"
        CLOSED = "CLOSED", "Encerrada"

    name = models.CharField("nome", max_length=150)
    deadline = models.DateField("prazo")
    status = models.CharField("status", max_length=10, choices=Status.choices, default=Status.OPEN)
    opened_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="aberta por",
        related_name="opened_inventory_audits",
        on_delete=models.PROTECT,
    )
    opened_at = models.DateTimeField("aberta em", auto_now_add=True)
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="encerrada por",
        related_name="closed_inventory_audits",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
    )
    closed_at = models.DateTimeField("encerrada em", blank=True, null=True)

    class Meta:
        ordering = ["-opened_at"]
        verbose_name = "auditoria de inventario"
        verbose_name_plural = "auditorias de inventario"
        constraints = [
            models.UniqueConstraint(
                fields=["status"],
                condition=models.Q(status="OPEN"),
                name="single_open_inventory_audit",
            )
        ]

    @property
    def is_overdue(self):
        return self.status == self.Status.OPEN and self.deadline < timezone.localdate()

    def __str__(self):
        return self.name


class InventoryAuditItem(models.Model):
    class Condition(models.TextChoices):
        GOOD = "GOOD", "Boa"
        FAIR = "FAIR", "Regular"
        POOR = "POOR", "Ruim"
        INOPERATIVE = "INOPERATIVE", "Inoperante"

    audit = models.ForeignKey(
        InventoryAudit,
        verbose_name="auditoria",
        related_name="audit_items",
        on_delete=models.CASCADE,
    )
    item = models.ForeignKey(
        InventoryItem,
        verbose_name="item",
        related_name="audit_records",
        on_delete=models.PROTECT,
    )
    snapshot_name = models.CharField("nome registrado", max_length=150)
    snapshot_department = models.CharField("departamento registrado", max_length=180, blank=True)
    snapshot_responsible_person = models.CharField("responsavel registrado", max_length=150, blank=True)
    snapshot_status = models.CharField("status registrado", max_length=20, choices=InventoryItem.Status.choices)
    snapshot_tombo_1 = models.CharField("tombo 1 registrado", max_length=80, blank=True)
    snapshot_tombo_2 = models.CharField("tombo 2 registrado", max_length=80, blank=True)
    snapshot_tombo_3 = models.CharField("tombo 3 registrado", max_length=80, blank=True)
    located = models.BooleanField("equipamento localizado", blank=True, null=True)
    condition = models.CharField("condicao", max_length=20, choices=Condition.choices, blank=True)
    found_department = models.ForeignKey(
        Department,
        verbose_name="departamento encontrado",
        related_name="audit_findings",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    found_responsible_person = models.CharField("responsavel encontrado", max_length=150, blank=True)
    observation = models.TextField("observacao", blank=True)
    evidence_image = models.ImageField("foto da conferencia", upload_to="inventory/audits/%Y/%m/", blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="conferido por",
        related_name="verified_inventory_items",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
    )
    verified_at = models.DateTimeField("conferido em", blank=True, null=True)
    reviewed = models.BooleanField("revisado", default=False)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="revisado por",
        related_name="reviewed_inventory_items",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
    )
    reviewed_at = models.DateTimeField("revisado em", blank=True, null=True)
    applied_department = models.BooleanField("departamento aplicado", default=False)
    applied_responsible_person = models.BooleanField("responsavel aplicado", default=False)
    applied_status = models.CharField("status aplicado", max_length=20, choices=InventoryItem.Status.choices, blank=True)
    movement = models.OneToOneField(
        "InventoryItemMovement",
        verbose_name="movimentacao gerada",
        related_name="audit_record",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    class Meta:
        ordering = ["snapshot_name"]
        verbose_name = "item de auditoria"
        verbose_name_plural = "itens de auditoria"
        constraints = [
            models.UniqueConstraint(fields=["audit", "item"], name="unique_item_per_audit")
        ]

    @property
    def is_verified(self):
        return self.verified_at is not None

    @property
    def has_discrepancy(self):
        if not self.is_verified:
            return False
        found_department = str(self.found_department) if self.found_department else ""
        return (
            self.located is False
            or self.condition != self.Condition.GOOD
            or found_department != self.snapshot_department
            or self.found_responsible_person != self.snapshot_responsible_person
        )

    def __str__(self):
        return f"{self.audit}: {self.snapshot_name}"


class InventoryItemMovement(models.Model):
    item = models.ForeignKey(
        InventoryItem,
        verbose_name="item",
        related_name="movements",
        on_delete=models.PROTECT,
    )
    reason = models.CharField("motivo", max_length=200)
    previous_department = models.CharField("departamento anterior", max_length=180, blank=True)
    new_department = models.CharField("novo departamento", max_length=180, blank=True)
    previous_responsible_person = models.CharField("responsavel anterior", max_length=150, blank=True)
    new_responsible_person = models.CharField("novo responsavel", max_length=150, blank=True)
    previous_status = models.CharField("status anterior", max_length=20, choices=InventoryItem.Status.choices)
    new_status = models.CharField("novo status", max_length=20, choices=InventoryItem.Status.choices)
    observation = models.TextField("observacao", blank=True)
    photo = models.ImageField("foto da movimentacao", upload_to="inventory/movements/photos/%Y/%m/")
    return_caution_document = models.FileField(
        "cautela de devolucao",
        upload_to="inventory/movements/cautions/%Y/%m/",
        blank=True,
    )
    delivery_caution_document = models.FileField(
        "cautela de entrega",
        upload_to="inventory/movements/cautions/%Y/%m/",
    )
    moved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="movimentado por",
        related_name="inventory_movements",
        on_delete=models.PROTECT,
    )
    moved_at = models.DateTimeField("movimentado em", auto_now_add=True)

    class Meta:
        ordering = ["-moved_at"]
        verbose_name = "movimentacao de item"
        verbose_name_plural = "movimentacoes de itens"

    def __str__(self):
        return f"{self.item} - {self.moved_at:%d/%m/%Y %H:%M}"
