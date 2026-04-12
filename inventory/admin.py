from django.contrib import admin

from .models import InventoryImage, InventoryItem


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
        "location",
        "responsible_person",
        "tombo_1",
        "updated_at",
    )
    list_filter = ("category", "status")
    search_fields = (
        "name",
        "description",
        "location",
        "responsible_person",
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
