from django.contrib import admin
from django.contrib.gis import admin as gis_admin

from safers.aois.constants import NAMED_AOIS

from safers.cameras.models import Camera


@admin.register(Camera)
class CameraAdmin(gis_admin.GeoModelAdmin):
    fields = (
        "id",
        "is_active",
        "camera_id",
        "name",
        "model",
        "owner",
        "nation",
        "last_update",
        "direction",
        "altitude",
        "geometry",
    )
    list_display = (
        "camera_id",
        "get_n_camera_media_for_list_display",
        "last_update",
        "is_active",
    )
    list_filter = (
        "is_active",
        "model",
        "owner",
        "nation",
    )
    ordering = ("camera_id", )
    readonly_fields = ("id", )
    search_fields = ("name", )

    default_lat = NAMED_AOIS["rome"].latitude
    default_lon = NAMED_AOIS["rome"].longitude
    default_zoom = point_zoom = 5

    @admin.display(description="N MEDIA")
    def get_n_camera_media_for_list_display(self, obj):
        return obj.media.count()
