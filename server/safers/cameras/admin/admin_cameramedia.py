from django.contrib import admin
from django.contrib.gis import admin as gis_admin

from safers.core.admin import get_clickable_fk_list_display, get_clickable_m2m_list_display

from safers.aois.constants import NAMED_AOIS

from safers.cameras.models import CameraMedia, CameraMediaFireClass, CameraMediaTag


@admin.register(CameraMediaFireClass)
class CameraMediaFireClassAdmin(admin.ModelAdmin):
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


@admin.register(CameraMediaTag)
class CameraMediaTagAdmin(admin.ModelAdmin):
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
        "tags",
        "fire_classes",
        "direction",
        "distance",
        "geometry",
    )
    filter_horizontal = (
        "tags",
        "fire_classes",
    )
    list_display = (
        "id",
        "timestamp",
        "type",
        "get_camera_for_list_display",
        "get_tags_for_list_display",
    )
    list_filter = (
        "camera",
        "type",
        "tags",
        "fire_classes",
    )
    readonly_fields = (
        "id",
        "created",
        "modified",
    )

    def get_queryset(self, request):
        # pre-fetching m2m fields that are used in list_displays
        queryset = super().get_queryset(request)
        return queryset.prefetch_related("tags")

    @admin.display(description="CAMERA")
    def get_camera_for_list_display(self, obj):
        return get_clickable_fk_list_display(obj.camera)

    @admin.display(description="TAGS")
    def get_tags_for_list_display(self, obj):
        return get_clickable_m2m_list_display(CameraMediaTag, obj.tags.all())
