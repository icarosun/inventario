import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Department, InventoryImage, InventoryItem


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
