from django.contrib import admin, messages
from django.contrib.gis import admin as gis_admin
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import JSONField
from django.forms import ModelForm, BaseInlineFormSet
from django.utils.translation import gettext_lazy as _

from safers.aois.constants import NAMED_AOIS

from safers.core.admin import JSONAdminWidget

from safers.data.models import MapRequest, DataType


class MapRequestStatusFilterTypes(models.TextChoices):

    ALL_NONE = "ALL_NONE", _("All: None")
    ALL_PROCESSING = "ALL_PROCESSING", _("All: Processing")
    ALL_FAILED = "ALL_FAILED", _("All: Failed")
    ALL_AVAILABLE = "ALL_AVAILABLE", _("All: Available")
    ANY_NONE = "ANY NONE", _("Any: None")
    ANY_PROCESSING = "ANY_PROCESSING", _("Any: Processing")
    ANY_FAILED = "ANY_FAILED", _("Any: Failed")
    ANY_AVAILABLE = "ANY_AVAILABLE", _("Any: Available")
    NONE_NONE = "NONE_NONE", _("None: None")
    NONE_PROCESSING = "NONE_PROCESSING", _("None: Processing")
    NONE_FAILED = "NONE_FAILED", _("None: Failed")
    NONE_AVAILABLE = "NONE_AVAILABLE", _("None: Available")


class MapRequestStatusFilter(admin.SimpleListFilter):
    parameter_name = "status"
    title = "statuses of MapRequestDataTypes"

    def lookups(self, request, model_admin):
        return MapRequestStatusFilterTypes.choices

    def queryset(self, request, qs):
        value = self.value()
        if value == MapRequestStatusFilterTypes.ALL_NONE:
            qs = qs.all_layers_none()
        elif value == MapRequestStatusFilterTypes.ALL_PROCESSING:
            qs = qs.all_layers_processing()
        elif value == MapRequestStatusFilterTypes.ALL_FAILED:
            qs = qs.all_layers_failed()
        elif value == MapRequestStatusFilterTypes.ALL_AVAILABLE:
            qs = qs.all_layers_available()
        elif value == MapRequestStatusFilterTypes.ANY_NONE:
            qs = qs.any_layers_none()
        elif value == MapRequestStatusFilterTypes.ANY_PROCESSING:
            qs = qs.any_layers_processing()
        elif value == MapRequestStatusFilterTypes.ANY_FAILED:
            qs = qs.any_layers_failed()
        elif value == MapRequestStatusFilterTypes.ANY_AVAILABLE:
            qs = qs.any_layers_available()
        elif value == MapRequestStatusFilterTypes.NONE_NONE:
            qs = qs.none_layers_none()
        elif value == MapRequestStatusFilterTypes.NONE_PROCESSING:
            qs = qs.none_layers_processing()
        elif value == MapRequestStatusFilterTypes.NONE_FAILED:
            qs = qs.none_layers_failed()
        elif value == MapRequestStatusFilterTypes.NONE_AVAILABLE:
            qs = qs.none_layers_available()
        return qs


class MapRequestDataTypeAdminFormSet(BaseInlineFormSet):
    """
    Using a custom formset to do some extra validation on all data_types at once
    """
    def clean(self):
        super().clean()
        data_types = []
        for form in self.forms:
            if form.is_valid() and not form.cleaned_data.get("DELETE"):
                data_types.append(form.cleaned_data["data_type"])

        if len(data_types) == 0:
            raise ValidationError(
                "A MapRequest must have at least one DataType."
            )

        if len(data_types) != len(set(data_types)):
            raise ValidationError(
                "A single MapRequest cannot have duplicate DataTypes"
            )

        if len(set([data_type.group for data_type in data_types])) != 1:
            raise ValidationError(
                "All DataTypes in a single MapRequest must belong to the same group."
            )


class MapRequestDataTypeAdminForm(ModelForm):
    """
    Using a custom form to constrain the data_types M2M relationship targets
    """
    class Meta:
        model = MapRequest.data_types.through
        fields = (
            "data_type",
            "status",
            "message",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["data_type"].queryset = DataType.objects.on_demand(
        ).order_by("group", "subgroup", "datatype_id")


class MapRequestDataTypeInline(admin.TabularInline):
    model = MapRequest.data_types.through
    form = MapRequestDataTypeAdminForm
    formset = MapRequestDataTypeAdminFormSet
    readonly_fields = (
        "created",
        "modified",
    )
    extra = 0


class MapRequestAdminForm(ModelForm):
    """
    Using a custom form to prevent geometry_wkt & geometry_extent from being manually edited
    """
    class Meta:
        model = MapRequest
        fields = (
            "title",
            "parameters",
            "geometry",
            "geometry_wkt",
            "geometry_extent",
            "geometry_extent_str",
            "user",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in [
            "geometry_wkt", "geometry_extent", "geometry_extent_str"
        ]:
            self.fields[field_name].widget.attrs.update({
                "readonly": True, "disbled": True
            })


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
    inlines = (MapRequestDataTypeInline, )
    list_display = (
        "request_id",
        "title",
        "category",
        "created",
        "get_statuses_for_list_view",
    )
    list_filter = (MapRequestStatusFilter, )
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

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.prefetch_related("map_request_data_types")

    @admin.display(description="statuses")
    def get_statuses_for_list_view(self, obj):
        statuses = obj.map_request_data_types.values_list("status", flat=True)
        return ", ".join([status or "NONE" for status in statuses])

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
