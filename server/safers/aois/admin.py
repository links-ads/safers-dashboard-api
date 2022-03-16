from django.contrib import admin
from django.contrib.gis.admin import GeoModelAdmin

from safers.aois.models import Aoi


@admin.register(Aoi)
class AoiAdmin(GeoModelAdmin):
    list_display = (
        "name",
        "is_active",
    )
    list_editable = ("is_active", )
    list_filter = ("is_active", )
    search_fields = ("name", )
