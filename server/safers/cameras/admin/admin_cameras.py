from django.contrib import admin
from django.contrib.gis import admin as gis_admin

from safers.aois.constants import NAMED_AOIS

from safers.cameras.models import Camera


@admin.register(Camera)
class CameraAdmin(gis_admin.GeoModelAdmin):
    actions = ("recalculate_last_update", )
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
        # I AM HERE
        try:
            return obj.media.count()
        except Exception as e:
            print(e)

    @admin.display(description="Recalculate last_update of selected Cameras")
    def recalculate_last_update(self, request, queryset):

        for obj in queryset:

            obj.recalculate_last_update()

            msg = f"set 'last_update' of {obj} to {obj.last_update}."
            self.message_user(request, msg)