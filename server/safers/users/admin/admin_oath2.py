from django.contrib import admin
from django.db.models import JSONField

from safers.core.admin import JSONAdminWidget

from safers.users.models import Oauth2User


@admin.register(Oauth2User)
class Oauth2UserAdmin(admin.ModelAdmin):
    formfield_overrides = {JSONField: {"widget": JSONAdminWidget}}
    list_display = (
        "user",
        "modified",
    )
    list_filter = ("user", )
    readonly_fields = (
        "created",
        "modified",
    )
    search_fields = ("user", )
