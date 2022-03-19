from django.contrib import admin
from django.contrib.gis import admin as gis_admin

from safers.alerts.models import Alert


@admin.register(Alert)
class AlertAdmin(gis_admin.GeoModelAdmin):
    fields = (
        "id",
        "hash",
        "timestamp",
        "description",
        "source",
        "status",
        "media",
        "geometry",
        "bounding_box",
    )
    list_filter = ("favorited_users", )
    readonly_fields = (
        "id",
        "hash",
        "bounding_box",
    )
