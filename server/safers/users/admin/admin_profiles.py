from django.contrib import admin

from safers.core.admin import get_clickable_fk_list_display, CannotDeleteModelAdminBase

from safers.users.models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(CannotDeleteModelAdminBase, admin.ModelAdmin):

    list_display = (
        "get_name_for_list_display",
        "get_user_for_list_display",
    )
    readonly_fields = ("id", )
    search_fields = (
        "user__name",
        "user__email",
    )

    def get_name_for_list_display(self, obj):
        return str(obj)

    get_name_for_list_display.short_description = "PROFILE"

    def get_user_for_list_display(self, obj):
        return get_clickable_fk_list_display(obj.user)

    get_user_for_list_display.short_description = "USER"
