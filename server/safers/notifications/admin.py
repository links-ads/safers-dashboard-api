import copy

from django.contrib import admin
from django.contrib.gis import admin as gis_admin
from django.contrib.admin.options import FORMFIELD_FOR_DBFIELD_DEFAULTS

from django.db.models import JSONField
from django.utils.html import mark_safe

from safers.core.admin import JSONAdminWidget
from safers.aois.constants import NAMED_AOIS
from safers.notifications.models import Notification, NotificationGeometry


class NotificationGeometryAdminInline(
    gis_admin.GeoModelAdmin, admin.TabularInline
):
    model = NotificationGeometry
    extra = 0
    fields = ("geometry", "description")
    verbose_name_plural = mark_safe(
        "<b>Geometries:</b> <i>the individual geometries corresponding to this notification</i>"
    )

    default_lat = NAMED_AOIS["rome"].latitude
    default_lon = NAMED_AOIS["rome"].longitude
    default_zoom = 4

    def __init__(self, parent_model, admin_site):

        # InlineModelAdmin.__init__
        self.admin_site = admin_site
        self.parent_model = parent_model
        self.opts = self.model._meta
        self.has_registered_model = admin_site.is_registered(self.model)

        # BaseModelAdmin.__init__
        overrides = copy.deepcopy(FORMFIELD_FOR_DBFIELD_DEFAULTS)
        for k, v in self.formfield_overrides.items():
            overrides.setdefault(k, {}).update(v)
        self.formfield_overrides = overrides


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    fields = (
        "id",
        "created",
        "timestamp",
        "status",
        "source",
        "scope",
        "category",
        "event",
        "urgency",
        "severity",
        "certainty",
        "description",
        "message",
    )
    formfield_overrides = {
        JSONField: {
            "widget": JSONAdminWidget
        },
    }
    inlines = (NotificationGeometryAdminInline, )
    list_display = (
        "id",
        "created",
    )
    ordering = ("-created", )
    readonly_fields = (
        "id",
        "created",
    )
