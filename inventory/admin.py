from django.contrib import admin

from .models import Department, InventoryImage, InventoryItem


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


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
