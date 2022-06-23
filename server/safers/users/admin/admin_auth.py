from django.contrib import admin

from knox.models import AuthToken


class KnoxTokenAdmin(admin.ModelAdmin):
    list_display = [
        "digest",
        "user",
        "created",
        "expiry",
    ]
    list_filter = ["user"]
    raw_id_fields = ["user"]


try:
    admin.site.unregister(AuthToken)
except admin.sites.NotRegistered:
    pass
admin.site.register(AuthToken, KnoxTokenAdmin)
