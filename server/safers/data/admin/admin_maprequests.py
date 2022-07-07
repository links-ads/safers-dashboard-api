from django.contrib import admin, messages
from django.contrib.gis import admin as gis_admin
from django.core.exceptions import ValidationError
from django.db.models import JSONField
from django.forms import ModelForm

from safers.aois.constants import NAMED_AOIS

from safers.core.admin import JSONAdminWidget

from safers.data.models import MapRequest, DataType


class MapRequestAdminForm(ModelForm):
    """
    Using a custom form to constrain the data_types M2M relationship targets
    and prevent geometry_wkt from being manually edited
    """
    class Meta:
        model = MapRequest
        fields = (
            "title",
            "status",
            "data_types",
            "parameters",
            "geometry",
            "geometry_wkt",
            "user",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["data_types"].queryset = DataType.objects.on_demand()
        self.fields["geometry_wkt"].widget.attrs.update({
            "readonly": True, "disbled": True
        })

    def clean_data_types(self):
        data_types = self.cleaned_data["data_types"]
        data_types_groups = data_types.values("group").distinct()
        if data_types_groups.count() != 1:
            raise ValidationError(
                "All DataTypes in a single MapRequest must belong to the same group."
            )

        return data_types


@admin.register(MapRequest)
class MapRequestAdmin(gis_admin.GeoModelAdmin):
    actions = (
        "invoke",
        "revoke",
    )
    date_hierarchy = "created"
    form = MapRequestAdminForm
    formfield_overrides = {
        JSONField: {
            "widget": JSONAdminWidget
        },
    }
    list_display = (
        "request_id",
        "created",
        "status",
    )
    list_filter = ("status", )
    ordering = ("-created", )
    readonly_fields = (
        "id",
        "request_id",
        "created",
        "modified",
    )

    default_lat = NAMED_AOIS["rome"].latitude
    default_lon = NAMED_AOIS["rome"].longitude
    default_zoom = point_zoom = 5

    @admin.display(description="Invoke MapRequest")
    def invoke(self, request, queryset):
        for map_request in queryset:
            try:
                map_request.invoke()
            except Exception as e:
                msg = f"unable to invoke map_request '{map_request.request_id}': {e}"
                self.message_user(request, msg, messages.ERROR)
                continue

            msg = f"invoked map_request '{map_request.request_id}'"
            self.message_user(request, msg, messages.INFO)

    @admin.display(description="Revoke MapRequest")
    def revoke(self, request, queryset):
        for map_request in queryset:
            try:
                map_request.revoke()
            except Exception as e:
                msg = f"unable to revoke map_request '{map_request.request_id}': {e}"
                self.message_user(request, msg, messages.ERROR)
                continue

            msg = f"revoked map_request '{map_request.request_id}'"
            self.message_user(request, msg, messages.INFO)
