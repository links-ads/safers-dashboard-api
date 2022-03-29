from django.contrib import admin
from django.contrib.gis import admin as gis_admin
from django.db.models import JSONField

from safers.core.admin import JSONAdminWidget
from safers.social.models import Tweet


@admin.register(Tweet)
class TweetAdmin(gis_admin.GeoModelAdmin):
    formfield_overrides = {JSONField: {"widget": JSONAdminWidget}}
    fields = (
        "id",
        "hash",
        "external_id",
        "type",
        "category",
        "start_date",
        "end_date",
        "data",
        "geometry",
        "bounding_box",
    )
    list_display = ("external_id", )
    readonly_fields = (
        "id",
        "hash",
        "bounding_box",
    )
