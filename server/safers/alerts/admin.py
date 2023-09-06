import copy

from django.contrib import admin
from django.contrib.gis import admin as gis_admin
from django.contrib.gis.forms import fields as gis_fields
from django.contrib.gis.forms import widgets as gis_widgets
from django.contrib.gis.gdal import OGRGeomType
from django.contrib.admin.options import FORMFIELD_FOR_DBFIELD_DEFAULTS
from django.forms import ModelForm

from django.db.models import JSONField
from django.utils.html import mark_safe

from safers.core.admin import JSONAdminWidget
from safers.aois.constants import NAMED_AOIS
from safers.alerts.models import Alert, AlertGeometry

# TODO: UNABLE TO GET THIS WORKING QUITE RIGHT...
# TODO: https://stackoverflow.com/questions/4720247/django-admin-inlines-with-geomodeladmin
# TODO: https://stackoverflow.com/questions/32037375/geodjango-can-i-use-osmgeoadmin-in-an-inline-in-the-user-admin
# TODO: https://stackoverflow.com/questions/72125303/in-geodjango-use-geomodeladmin-as-a-stackedinline-in-the-django-admin

# class AlertGeometryAdminForm(ModelForm):
#     class Meta:
#         model = AlertGeometry
#         fields = (
#             "geometry",
#             "description",
#             "bounding_box",
#             "center",
#         )
#         readonly_fields = (
#             "bounding_box",
#             "center",
#         )

#     geometry = gis_fields.GeometryField(
#         widget=gis_widgets.OpenLayersWidget(attrs={})
#     )

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         geometry_field = self.fields["geometry"]
#         geometry_field.name = "geometry"
#         geometry_field.widget = AlertGeometryAdminForm.geometry_widget_factory(
#             geometry_field
#         )

#     @classmethod
#     def geometry_widget_factory(cls, field):

#         is_collection = field.geom_type in (
#             "MULTIPOINT",
#             "MULTILINESTRING",
#             "MULTIPOLYGON",
#             "GEOMETRYCOLLECTION",
#         )
#         if is_collection:
#             if field.geom_type == "GEOMETRYCOLLECTION":
#                 collection_type = "Any"
#             else:
#                 collection_type = OGRGeomType(
#                     field.geom_type.replace("MULTI", "")
#                 )
#         else:
#             collection_type = "None"

#         class OLMap(gis_widgets.OpenLayersWidget):
#             template_name = "gis/admin/openlayers.html"
#             geom_type = field.geom_type

#             params = {
#                 "default_lon": NAMED_AOIS["rome"].longitude,
#                 "default_lat": NAMED_AOIS["rome"].latitude,
#                 "default_zoom": 5,
#                 "display_wkt": False,
#                 "geom_type": OGRGeomType(field.geom_type),
#                 "field_name": field.name,
#                 "is_collection": is_collection,
#                 "scrollable": True,
#                 "layerswitcher": True,
#                 "collection_type": collection_type,
#                 "is_generic": field.geom_type == "GEOMETRY",
#                 "is_linestring": field.geom_type in ("LINESTRING", "MULTILINESTRING"),
#                 "is_polygon": field.geom_type in ("POLYGON", "MULTIPOLYGON"),
#                 "is_point": field.geom_type in ("POINT", "MULTIPOINT"),
#                 "num_zoom": 18,
#                 "max_zoom": False,
#                 "min_zoom": False,
#                 "units": False,  # likely should get from object
#                 "max_resolution": False,
#                 "max_extent": False,
#                 "modifiable": True,
#                 "mouse_position": True,
#                 "scale_text": True,
#                 "map_width": 600,
#                 "map_height": 400,
#                 "point_zoom": 5,
#                 "srid": 4326,
#                 "display_srid": False,
#                 "wms_url": "http://vmap0.tiles.osgeo.org/wms/vmap0",
#                 "wms_layer": "basic",
#                 "wms_name": "OpenLayers WMS",
#                 "wms_options": {"format": "image/jpeg"},
#                 "debug": False,
#             }  # yapf: disable

#         return OLMap()


class AlertGeometryAdminInline(gis_admin.GeoModelAdmin, admin.TabularInline):
    model = AlertGeometry
    extra = 1
    # form = AlertGeometryAdminForm
    fields = (
        "geometry",
        "description",
    )
    # formfield_overrides = {
    #     gis_fields.GeometryField: {
    #         "widget": gis_widgets.OpenLayersWidget
    #     }
    # }
    verbose_name = "Alert Geometry"
    verbose_name_plural = mark_safe(
        "<b>Geometries:</b> <i>the individual geometries corresponding to this alert</i>"
    )

    default_lat = NAMED_AOIS["rome"].latitude
    default_lon = NAMED_AOIS["rome"].longitude
    default_zoom = point_zoom = 5

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


@admin.register(Alert)
class AlertAdmin(gis_admin.GeoModelAdmin):
    fields = (
        "id",
        "created",
        "modified",
        "type",
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
        "information",
        # "geometry_collection",
        "center",
        "bounding_box",
        "country",

    )
    formfield_overrides = {
        JSONField: {
            "widget": JSONAdminWidget
        },
    }
    inlines = (AlertGeometryAdminInline, )
    list_display = (
        "name",
        "id",
        "type",
        "source",
        "category",
        "timestamp",
        "created",
    )
    list_filter = (
        "favorited_users",
        "source",
        "type",
    )
    ordering = ("-created", )
    readonly_fields = (
        "id",
        "created",
        "modified",
    )

    default_lat = NAMED_AOIS["rome"].latitude
    default_lon = NAMED_AOIS["rome"].longitude
    default_zoom = point_zoom = 5
    modifiable = False
