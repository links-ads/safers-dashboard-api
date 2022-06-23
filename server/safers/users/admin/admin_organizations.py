from django.contrib import admin

from safers.users.models import Organization


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    fields = (
        "id",
        "name",
        "description",
        "is_active",
    )
    list_display = (
        "name",
        "id",
        "is_active",
    )
    list_editable = ("is_active", )
    list_filter = ("is_active", )
    readonly_fields = ("id", )
    search_fields = ("name", )
