import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import (
    Department,
    InventoryAudit,
    InventoryAuditItem,
    InventoryImage,
    InventoryItem,
)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class InventoryViewsTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="usuario",
            password="senha-forte-123",
        )
        self.staff = get_user_model().objects.create_user(
            username="admin",
            password="senha-forte-123",
            is_staff=True,
        )

    def create_item(self):
        return InventoryItem.objects.create(
            name="Notebook Dell",
            category=InventoryItem.Category.TI,
            status=InventoryItem.Status.ACTIVE,
            tombo_1="A1",
            tombo_2="B2",
            tombo_3="C3",
            specs={"memoria": "16GB"},
            created_by=self.user,
            updated_by=self.user,
        )

    def test_login_required_for_item_list(self):
        response = self.client.get(reverse("inventory:item_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])

    def test_authenticated_user_can_create_item_with_tombos_and_specs(self):
        department = Department.objects.create(name="Sala TI", acronym="STI")
        self.client.login(username="usuario", password="senha-forte-123")
        response = self.client.post(
            reverse("inventory:item_create"),
            {
                "name": "Desktop HP",
                "category": InventoryItem.Category.TI,
                "description": "Uso administrativo",
                "department": department.pk,
                "responsible_person": "Maria",
                "immediate_supervisor": "Joao",
                "status": InventoryItem.Status.ACTIVE,
                "tombo_1": "T1",
                "tombo_2": "T2",
                "tombo_3": "T3",
                "specs": '{"processador": "i5"}',
            },
        )
        item = InventoryItem.objects.get(name="Desktop HP")
        self.assertRedirects(response, reverse("inventory:item_detail", args=[item.pk]))
        self.assertEqual(item.department, department)
        self.assertEqual(item.tombo_1, "T1")
        self.assertEqual(item.tombo_2, "T2")
        self.assertEqual(item.tombo_3, "T3")
        self.assertEqual(item.immediate_supervisor, "Joao")
        self.assertEqual(item.specs["processador"], "i5")
        self.assertEqual(item.created_by, self.user)

    def test_authenticated_user_can_manage_departments(self):
        self.client.login(username="usuario", password="senha-forte-123")
        create_response = self.client.post(
            reverse("inventory:department_create"),
            {"name": "Logistica", "acronym": "LOG"},
        )
        department = Department.objects.get(name="Logistica")
        self.assertRedirects(create_response, reverse("inventory:department_list"))

        update_response = self.client.post(
            reverse("inventory:department_update", args=[department.pk]),
            {"name": "Almoxarifado", "acronym": "ALM"},
        )
        self.assertRedirects(update_response, reverse("inventory:department_list"))
        department.refresh_from_db()
        self.assertEqual(department.name, "Almoxarifado")
        self.assertEqual(department.acronym, "ALM")

        delete_response = self.client.post(
            reverse("inventory:department_delete", args=[department.pk]),
        )
        self.assertRedirects(delete_response, reverse("inventory:department_list"))
        self.assertFalse(Department.objects.filter(pk=department.pk).exists())

    def test_item_detail_shows_serial_number_label(self):
        item = self.create_item()
        self.client.login(username="usuario", password="senha-forte-123")
        response = self.client.get(reverse("inventory:item_detail", args=[item.pk]))
        self.assertContains(response, "Tombo 3 ou numero de serie")

    def test_non_staff_user_cannot_delete_item(self):
        item = self.create_item()
        self.client.login(username="usuario", password="senha-forte-123")
        response = self.client.post(reverse("inventory:item_delete", args=[item.pk]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(InventoryItem.objects.filter(pk=item.pk).exists())

    def test_staff_user_can_delete_item(self):
        item = self.create_item()
        self.client.login(username="admin", password="senha-forte-123")
        response = self.client.post(reverse("inventory:item_delete", args=[item.pk]))
        self.assertRedirects(response, reverse("inventory:item_list"))
        self.assertFalse(InventoryItem.objects.filter(pk=item.pk).exists())

    def test_authenticated_user_can_upload_item_image(self):
        item = self.create_item()
        image = SimpleUploadedFile(
            "item.gif",
            b"GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;",
            content_type="image/gif",
        )
        self.client.login(username="usuario", password="senha-forte-123")
        response = self.client.post(
            reverse("inventory:item_image_create", args=[item.pk]),
            {"image": image, "caption": "Frente"},
        )
        self.assertRedirects(response, reverse("inventory:item_detail", args=[item.pk]))
        self.assertEqual(InventoryImage.objects.filter(item=item).count(), 1)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class InventoryAuditTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="auditor", password="senha-forte-123")
        self.staff = get_user_model().objects.create_user(username="gestor", password="senha-forte-123", is_staff=True)
        self.department = Department.objects.create(name="Tecnologia", acronym="TI")
        self.other_department = Department.objects.create(name="Administracao", acronym="ADM")
        self.item = InventoryItem.objects.create(
            name="Notebook",
            category=InventoryItem.Category.TI,
            department=self.department,
            responsible_person="Maria",
            status=InventoryItem.Status.ACTIVE,
            created_by=self.staff,
            updated_by=self.staff,
        )
        self.stored_item = InventoryItem.objects.create(
            name="Monitor em estoque",
            category=InventoryItem.Category.TI,
            status=InventoryItem.Status.STORED,
            created_by=self.staff,
            updated_by=self.staff,
        )

    def image(self, name="evidencia.gif"):
        return SimpleUploadedFile(
            name,
            b"GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;",
            content_type="image/gif",
        )

    def caution(self, name="cautela.txt"):
        return SimpleUploadedFile(name, b"cautela assinada", content_type="text/plain")

    def open_audit(self):
        self.client.login(username="gestor", password="senha-forte-123")
        response = self.client.post(
            reverse("inventory:audit_create"),
            {"name": "Auditoria 2026.1", "deadline": "2026-12-31"},
        )
        audit = InventoryAudit.objects.get(name="Auditoria 2026.1")
        self.assertRedirects(response, reverse("inventory:audit_detail", args=[audit.pk]))
        return audit

    def test_staff_opens_audit_with_snapshot_of_active_items_only(self):
        audit = self.open_audit()
        self.assertEqual(audit.audit_items.count(), 1)
        record = audit.audit_items.get()
        self.assertEqual(record.item, self.item)
        self.assertEqual(record.snapshot_department, "TI - Tecnologia")
        self.assertEqual(record.snapshot_responsible_person, "Maria")

    def test_cannot_open_two_audits_at_the_same_time(self):
        self.open_audit()
        response = self.client.post(
            reverse("inventory:audit_create"),
            {"name": "Outra auditoria", "deadline": "2027-01-31"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(InventoryAudit.objects.count(), 1)

    def test_user_confirms_item_without_discrepancy_and_staff_closes_audit(self):
        audit = self.open_audit()
        record = audit.audit_items.get()
        self.client.login(username="auditor", password="senha-forte-123")
        response = self.client.post(
            reverse("inventory:audit_verify", args=[record.pk]),
            {
                "located": "True",
                "condition": InventoryAuditItem.Condition.GOOD,
                "found_department": self.department.pk,
                "found_responsible_person": "Maria",
                "observation": "Equipamento conferido.",
            },
        )
        self.assertRedirects(response, reverse("inventory:audit_detail", args=[audit.pk]))
        record.refresh_from_db()
        self.assertTrue(record.is_verified)
        self.assertFalse(record.has_discrepancy)

        self.client.login(username="gestor", password="senha-forte-123")
        self.client.post(reverse("inventory:audit_close", args=[audit.pk]))
        audit.refresh_from_db()
        self.assertEqual(audit.status, InventoryAudit.Status.CLOSED)

    def test_divergence_review_updates_item_and_creates_movement_with_evidence(self):
        audit = self.open_audit()
        record = audit.audit_items.get()
        self.client.login(username="auditor", password="senha-forte-123")
        self.client.post(
            reverse("inventory:audit_verify", args=[record.pk]),
            {
                "located": "True",
                "condition": InventoryAuditItem.Condition.FAIR,
                "found_department": self.other_department.pk,
                "found_responsible_person": "Joao",
                "observation": "Transferido de setor.",
            },
        )
        record.refresh_from_db()
        self.assertTrue(record.has_discrepancy)

        self.client.login(username="gestor", password="senha-forte-123")
        response = self.client.post(
            reverse("inventory:audit_review", args=[record.pk]),
            {
                "apply_department": "on",
                "apply_responsible_person": "on",
                "applied_status": InventoryItem.Status.MAINTENANCE,
                "movement_photo": self.image(),
                "return_caution_document": self.caution("devolucao.txt"),
                "delivery_caution_document": self.caution("entrega.txt"),
            },
        )
        self.assertRedirects(response, reverse("inventory:audit_detail", args=[audit.pk]))
        record.refresh_from_db()
        self.item.refresh_from_db()
        self.assertTrue(record.reviewed)
        self.assertIsNotNone(record.movement)
        self.assertEqual(self.item.department, self.other_department)
        self.assertEqual(self.item.responsible_person, "Joao")
        self.assertEqual(self.item.status, InventoryItem.Status.MAINTENANCE)
        self.assertTrue(record.movement.photo.name)
        self.assertTrue(record.movement.return_caution_document.name)
        self.assertTrue(record.movement.delivery_caution_document.name)

    def test_audit_cannot_close_with_pending_items(self):
        audit = self.open_audit()
        response = self.client.post(reverse("inventory:audit_close", args=[audit.pk]))
        self.assertRedirects(response, reverse("inventory:audit_detail", args=[audit.pk]))
        audit.refresh_from_db()
        self.assertEqual(audit.status, InventoryAudit.Status.OPEN)

    def test_only_staff_can_export_csv(self):
        audit = self.open_audit()
        self.client.login(username="auditor", password="senha-forte-123")
        self.assertEqual(self.client.get(reverse("inventory:audit_export", args=[audit.pk])).status_code, 403)
        self.client.login(username="gestor", password="senha-forte-123")
        response = self.client.get(reverse("inventory:audit_export", args=[audit.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")

    def test_manual_movement_requires_delivery_caution(self):
        self.client.login(username="auditor", password="senha-forte-123")
        response = self.client.post(
            reverse("inventory:item_move", args=[self.item.pk]),
            {
                "department": self.other_department.pk,
                "responsible_person": "Carlos",
                "status": InventoryItem.Status.ACTIVE,
                "reason": "Mudanca sem entrega",
                "photo": self.image("movimento.gif"),
                "return_caution_document": self.caution("devolucao.txt"),
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("delivery_caution_document", response.context["form"].errors)
        self.assertFalse(self.item.movements.exists())

    def test_manual_movement_updates_item_and_appears_in_history(self):
        self.client.login(username="auditor", password="senha-forte-123")
        response = self.client.post(
            reverse("inventory:item_move", args=[self.item.pk]),
            {
                "department": self.other_department.pk,
                "responsible_person": "Carlos",
                "status": InventoryItem.Status.ACTIVE,
                "reason": "Mudanca de responsavel",
                "observation": "Cautela atualizada.",
                "photo": self.image("movimento.gif"),
                "return_caution_document": self.caution("devolucao.txt"),
                "delivery_caution_document": self.caution("entrega.txt"),
            },
        )
        self.assertRedirects(response, reverse("inventory:item_detail", args=[self.item.pk]))
        self.item.refresh_from_db()
        movement = self.item.movements.get()
        self.assertEqual(self.item.department, self.other_department)
        self.assertEqual(self.item.responsible_person, "Carlos")
        self.assertEqual(movement.previous_responsible_person, "Maria")
        detail = self.client.get(reverse("inventory:item_detail", args=[self.item.pk]))
        self.assertContains(detail, "Mudanca de responsavel")
