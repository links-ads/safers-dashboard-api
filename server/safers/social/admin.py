from django.contrib import admin
from django.contrib.gis import admin as gis_admin
from django.db.models import JSONField

from safers.core.admin import JSONAdminWidget, DateRangeListFilter

from safers.social.models import SocialEvent


@admin.register(SocialEvent)
class SocialEventAdmin(gis_admin.GeoModelAdmin):
    formfield_overrides = {JSONField: {"widget": JSONAdminWidget}}
    fields = (
        "id",
        "hash",
        "external_id",
        "category",
        "severity",
        "description",
        "start_date",
        "end_date",
        "data",
        "geometry",
        "bounding_box",
    )
    list_display = (
        "external_id",
        "get_description_for_list_display",
        "category",
        "severity",
        "start_date",
        "end_date",
    )
    list_filter = (
        "category",
        "severity",
        "start_date",
        "end_date",
        # ("start_date", DateRangeListFilter),
        # ("end_date", DateRangeListFilter),
    )
    readonly_fields = (
        "id",
        "hash",
        "bounding_box",
    )

    def get_description_for_list_display(self, obj):
        description = obj.description
        if description:
            MAX_LEN = 20
            return description[:MAX_LEN] + "..." \
                if len(description) > MAX_LEN else description

    get_description_for_list_display.short_description = "DESCRIPTION"
