from django.contrib import admin
from django.contrib.gis import admin as gis_admin
from django.db.models import JSONField

from safers.core.admin import JSONAdminWidget

from safers.rmq.models import Message


@admin.register(Message)
class MessageAdmin(gis_admin.GeoModelAdmin):
    formfield_overrides = {JSONField: {"widget": JSONAdminWidget}}

    fields = (
        "id",
        "timestamp",
        "routing_key",
        "status",
        "body",
    )
    list_display = (
        "id",
        "timestamp",
        "routing_key",
        "status",
    )
    list_filter = (
        "status",
        "timestamp",
    )
    readonly_fields = ("id", )
