from django.contrib import admin

from safers.core.admin import get_clickable_fk_list_display, CannotDeleteModelAdminBase

from safers.users.models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):

    list_display = (
        "get_name_for_list_display",
        "get_user_for_list_display",
    )
    readonly_fields = ("id", )
    search_fields = (
        "user__username",
        "user__email",
        "first_name",
        "last_name",
    )

    @admin.display(description="PROFILE")
    def get_name_for_list_display(self, obj):
        return str(obj)

    @admin.display(description="USER")
    def get_user_for_list_display(self, obj):
        return get_clickable_fk_list_display(obj.user)
