from django.urls import path

from . import views

app_name = "inventory"

urlpatterns = [
    path("", views.ItemListView.as_view(), name="item_list"),
    path("items/new/", views.ItemCreateView.as_view(), name="item_create"),
    path("items/<int:pk>/", views.ItemDetailView.as_view(), name="item_detail"),
    path("items/<int:pk>/edit/", views.ItemUpdateView.as_view(), name="item_update"),
    path("items/<int:pk>/delete/", views.ItemDeleteView.as_view(), name="item_delete"),
    path("items/<int:pk>/images/new/", views.add_item_image, name="item_image_create"),
    path("items/<int:pk>/move/", views.move_item, name="item_move"),
    path("departments/", views.DepartmentListView.as_view(), name="department_list"),
    path("departments/new/", views.DepartmentCreateView.as_view(), name="department_create"),
    path("departments/<int:pk>/edit/", views.DepartmentUpdateView.as_view(), name="department_update"),
    path("departments/<int:pk>/delete/", views.DepartmentDeleteView.as_view(), name="department_delete"),
    path("audits/", views.AuditListView.as_view(), name="audit_list"),
    path("audits/new/", views.AuditCreateView.as_view(), name="audit_create"),
    path("audits/<int:pk>/", views.AuditDetailView.as_view(), name="audit_detail"),
    path("audits/<int:pk>/close/", views.close_audit, name="audit_close"),
    path("audits/<int:pk>/export/", views.export_audit_csv, name="audit_export"),
    path("audit-items/<int:pk>/verify/", views.AuditVerificationView.as_view(), name="audit_verify"),
    path("audit-items/<int:pk>/review/", views.AuditReviewView.as_view(), name="audit_review"),
]
