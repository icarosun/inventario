from django.contrib import admin

from .models import Department, InventoryAudit, InventoryAuditItem, InventoryImage, InventoryItem, InventoryItemMovement


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "acronym")
    search_fields = ("name", "acronym")


class InventoryImageInline(admin.TabularInline):
    model = InventoryImage
    extra = 1


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    inlines = [InventoryImageInline]
    list_display = (
        "name",
        "category",
        "status",
        "department",
        "responsible_person",
        "immediate_supervisor",
        "tombo_1",
        "updated_at",
    )
    list_filter = ("category", "status", "department")
    search_fields = (
        "name",
        "description",
        "department__name",
        "responsible_person",
        "immediate_supervisor",
        "tombo_1",
        "tombo_2",
        "tombo_3",
    )
    readonly_fields = ("created_by", "updated_by", "created_at", "updated_at")

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(InventoryImage)
class InventoryImageAdmin(admin.ModelAdmin):
    list_display = ("item", "caption", "uploaded_at")
    search_fields = ("item__name", "caption")


@admin.register(InventoryAudit)
class InventoryAuditAdmin(admin.ModelAdmin):
    list_display = ("name", "status", "deadline", "opened_by", "opened_at", "closed_at")
    list_filter = ("status",)
    readonly_fields = ("opened_at", "closed_at")


@admin.register(InventoryAuditItem)
class InventoryAuditItemAdmin(admin.ModelAdmin):
    list_display = ("audit", "snapshot_name", "located", "condition", "verified_by", "reviewed")
    list_filter = ("audit", "located", "condition", "reviewed")
    search_fields = ("snapshot_name", "snapshot_tombo_1", "snapshot_tombo_2", "snapshot_tombo_3")


@admin.register(InventoryItemMovement)
class InventoryItemMovementAdmin(admin.ModelAdmin):
    list_display = ("item", "reason", "moved_by", "moved_at")
    search_fields = ("item__name", "reason", "observation")
    list_filter = ("new_status", "moved_at")
