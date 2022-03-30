from django.contrib import admin
from django.contrib.gis import admin as gis_admin
from django.db.models import JSONField

from safers.core.admin import JSONAdminWidget

from safers.chatbot.models import Report


@admin.register(Report)
class ReportAdmin(gis_admin.GeoModelAdmin):
    formfield_overrides = {JSONField: {"widget": JSONAdminWidget}}
    fields = (
        "id",
        "hash",
        "external_id",
        "data",
        "geometry",
        "bounding_box",
    )
    list_display = ("external_id", )
    list_filter = ()
    readonly_fields = (
        "id",
        "hash",
        "bounding_box",
    )
