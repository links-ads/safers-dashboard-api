from django.contrib import admin

from safers.auth.models import AccessToken, RefreshToken

LIST_DISPLAY_TOKEN_LENGTH = 64


class IsExpiredFilter(admin.SimpleListFilter):
    title = "is expired"
    parameter_name = "expired"

    def lookups(self, request, model_admin):
        return (
            ("Yes", "Yes"),
            ("No", "No"),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == "Yes":
            return queryset.expired()
        elif value == "No":
            return queryset.unexpired()
        return queryset


@admin.register(AccessToken)
class AccessTokenAdmin(admin.ModelAdmin):
    list_display = (
        "get_token_for_list_display",
        "created",
        "user",
        "get_expired_for_list_display",
    )
    list_filter = (
        "user",
        IsExpiredFilter,
    )
    readonly_fields = ("created", )

    @admin.display(description="TOKEN")
    def get_token_for_list_display(self, obj):
        """
        Show a snippet of the token in the admin list display
        """
        return obj.token[:LIST_DISPLAY_TOKEN_LENGTH]

    @admin.display(description="EXPIRED", boolean=True)
    def get_expired_for_list_display(self, obj):
        return obj.expired


@admin.register(RefreshToken)
class RefreshTokenAdmin(admin.ModelAdmin):
    list_display = (
        "get_token_for_list_display",
        "created",
        "user",
    )
    list_filter = ("user", )

    @admin.display(description="TOKEN")
    def get_token_for_list_display(self, obj):
        """
        Show a snippet of the token in the admin list display
        """
        return obj.token[:LIST_DISPLAY_TOKEN_LENGTH]