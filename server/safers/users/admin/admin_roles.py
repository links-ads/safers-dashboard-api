from django.contrib import admin

from safers.users.models import Role


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    fields = (
        "id",
        "role_id",
        "name",
        "label",
        "description",
        "is_default",
        "is_super",
        "is_active",
    )
    list_display = (
        "name",
        "role_id",
        "is_active",
    )
    list_editable = ("is_active", )
    list_filter = (
        "is_active",
        "is_default",
        "is_super",
    )
    ordering = ("role_id", )
    readonly_fields = ("id", )
    search_fields = ("name", "label")
