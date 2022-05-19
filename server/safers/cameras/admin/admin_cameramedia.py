from django.contrib import admin
from django.contrib.gis import admin as gis_admin

from safers.core.admin import get_clickable_fk_list_display

from safers.aois.constants import NAMED_AOIS

from safers.cameras.models import CameraMedia, CameraMediaFireClass


@admin.register(CameraMediaFireClass)
class CameraMediaSmokeColumnClassAdmin(gis_admin.GeoModelAdmin):
    fields = (
        "name",
        "description",
    )
    list_display = (
        "name",
        "get_n_camera_media_for_list_display",
    )
    ordering = ("name", )

    @admin.display(description="N MEDIA")
    def get_n_camera_media_for_list_display(self, obj):
        return obj.media.count()


@admin.register(CameraMedia)
class CameraMediaAdmin(gis_admin.GeoModelAdmin):
    date_hierarchy = "timestamp"
    fields = (
        "id",
        "camera",
        "timestamp",
        "created",
        "modified",
        "description",
        "url",
        "type",
        "is_smoke",
        "is_fire",
        "fire_classes",
        "direction",
        "distance",
        "geometry",
    )
    filter_horizontal = ("fire_classes", )
    list_display = (
        "id",
        "timestamp",
        "type",
        "is_smoke",
        "is_fire",
        "get_camera_for_list_display",
    )
    list_filter = (
        "camera",
        "type",
        "fire_classes",
    )
    readonly_fields = (
        "id",
        "created",
        "modified",
    )

    @admin.display(description="CAMERA")
    def get_camera_for_list_display(self, obj):
        return get_clickable_fk_list_display(obj.camera)
