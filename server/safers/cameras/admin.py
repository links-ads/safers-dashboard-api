from django.contrib import admin
from django.contrib.gis import admin as gis_admin

from safers.core.admin import get_clickable_fk_list_display, get_clickable_m2m_list_display

from safers.cameras.models import Camera, CameraMedia, CameraMediaTag


@admin.register(Camera)
class CameraAdmin(gis_admin.GeoModelAdmin):
    fields = (
        "id",
        "name",
        "last_update",
        "description",
        "geometry",
    )
    list_display = (
        "name",
        "get_n_camera_media_for_list_display",
    )
    readonly_fields = ("id", )

    @admin.display(description="N MEDIA")
    def get_n_camera_media_for_list_display(self, obj):
        return obj.media.count()


@admin.register(CameraMedia)
class CameraMediaAdmin(gis_admin.GeoModelAdmin):
    fields = (
        "id",
        "hash",
        "timestamp",
        "description",
        "camera",
        "smoke_column_class",
        "geographical_direction",
        "type",
        "tags",
        "geometry",
        "bounding_box",
    )
    filter_horizontal = ("tags", )
    list_display = (
        "id",
        "type",
        "get_camera_for_list_display",
        "get_camera_media_tags_for_list_display",
    )
    list_filter = (
        "camera",
        "type",
        "tags",  # "favorited_users",
    )
    readonly_fields = (
        "id",
        "hash",
        "bounding_box",
    )

    def get_queryset(self, request):
        # pre-fetching m2m fields that are used in list_displays
        queryset = super().get_queryset(request)
        return queryset.prefetch_related("tags")

    @admin.display(description="CAMERA")
    def get_camera_for_list_display(self, obj):
        return get_clickable_fk_list_display(obj.camera)

    @admin.display(description="TAGS")
    def get_camera_media_tags_for_list_display(self, obj):
        return get_clickable_m2m_list_display(CameraMediaTag, obj.tags.all())


@admin.register(CameraMediaTag)
class CameraMediaTagAdmin(gis_admin.GeoModelAdmin):
    fields = ("name", )
    list_display = (
        "name",
        "get_n_camera_media_for_list_display",
    )

    @admin.display(description="N MEDIA")
    def get_n_camera_media_for_list_display(self, obj):
        return obj.media.count()

    # TODO: INLINES