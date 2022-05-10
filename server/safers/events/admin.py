from django.contrib import admin
from django.contrib.gis import admin as gis_admin

from safers.events.models import Event


@admin.register(Event)
class EventAdmin(gis_admin.GeoModelAdmin):
    fields = (
        "id",
        "start_date",
        "end_date",
        "description",
        "people_affected",
        "causalties",
        "estimated_damage",
        "alerts",
        "geometry_collection",
        "bounding_box",
        "center",
    )
    filter_horizontal = ("alerts", )
    list_filter = ("favorited_users", )
    readonly_fields = ("id", )
