import json

from django.conf import settings
from django.contrib import admin, messages
from django.contrib.gis.admin import GeoModelAdmin
from django.forms import Form, FileField
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import path, reverse
from django.utils.html import format_html

from rest_framework.utils.encoders import JSONEncoder

from safers.aois.models import Aoi
from safers.aois.serializers import AoiSerializer


@admin.register(Aoi)
class AoiAdmin(GeoModelAdmin):
    fields = None
    fieldsets = (
        (
            "Actions",
            {
                "classes": ("collapse", ),
                "fields": (
                    "get_dump_geojson_for_detail_display",
                    "get_load_geojson_for_detail_display",
                ),
            },
        ),
        (
            None,
            {
                "fields": (
                    "id",
                    "name",
                    "description",
                    "country",
                    "zoom_level",
                    "midpoint",
                    "is_active",
                    "geometry",
                )
            },
        ),
    )  # yapf: disable
    readonly_fields = (
        "id",
        "get_dump_geojson_for_detail_display",
        "get_load_geojson_for_detail_display",
    )
    list_display = (
        "name",
        "is_active",
    )
    list_editable = ("is_active", )
    list_filter = ("is_active", )
    search_fields = ("name", )

    #############################################
    # some fns to help w/ custom detail actions #
    #############################################

    @property
    def url_basename(self):
        return self.model._meta.db_table

    def get_urls(self):
        urls = [
            path(
                "<slug:pk>/dump/",
                self.dump,
                name=f"{self.url_basename}_dump",
            ),
            path(
                "<slug:pk>/load/",
                self.load,
                name=f"{self.url_basename}_load",
            ),
        ] + super().get_urls()  # (order is important)
        return urls

    @admin.display(description="Export GeoJSON")
    def get_dump_geojson_for_detail_display(self, obj):
        if obj.pk:
            dump_description = "Export the AOI as a GeoJSON FeatureCollection."
            dump_url = reverse(f"admin:{self.url_basename}_dump", args=[obj.pk])
            return format_html(
                f"<a href='{dump_url}' title='{dump_description}'>Export</a>"
            )
        else:
            return format_html("----------")

    @admin.display(description="Import GeoJSON")
    def get_load_geojson_for_detail_display(self, obj):
        if obj.pk:
            load_description = "Import a GeoJSON FeatureCollection to update this AOI."
            load_url = reverse(f"admin:{self.url_basename}_load", args=[obj.pk])
            return format_html(
                f"<a href='{load_url}' title='{load_description}'>Import</a>"
            )
        else:
            return format_html("----------")

    ##################
    # detail actions #
    ##################

    # TODO: SHOULD PROBABLY FACTOR THIS OUT INTO A MIXIN

    def dump(self, request, pk):
        """
        Exports a serialization of an AOI
        """
        obj = get_object_or_404(Aoi, pk=pk)
        serializer = AoiSerializer(obj)

        response = JsonResponse(serializer.data, encoder=JSONEncoder)
        response.headers["Content-Disposition"] = \
            f"attachment; filename={str(obj)}.json"

        return response

    def load(self, request, pk):
        """
        Imports a serialization of an AOI
        """
        obj = get_object_or_404(Aoi, pk=pk)

        class LoadForm(Form):
            file = FileField(required=True, label="File to Import")

        if request.method == "GET":
            load_form = LoadForm()
        else:
            load_form = LoadForm(request.POST, request.FILES)

        if "apply" in request.POST:

            if load_form.is_valid():
                serializer = AoiSerializer(
                    instance=obj,
                    data=json.load(load_form.cleaned_data["file"])
                )
                try:
                    serializer.is_valid(raise_exception=True)
                    serializer.save()
                    self.message_user(
                        request, f"updated {obj}.", messages.SUCCESS
                    )
                    change_url = reverse(
                        f"admin:{self.url_basename}_change", args=[obj.pk]
                    )
                    return HttpResponseRedirect(change_url)

                except Exception as e:
                    self.message_user(request, str(e), messages.ERROR)

        context = {
            "obj": obj,
            "form": load_form,
            "site_header": getattr(settings, "ADMIN_SITE_HEADER", None),
            "site_title": getattr(settings, "ADMIN_SITE_TITLE", None),
            "index_title": getattr(settings, "ADMIN_INDEX_TITLE", None),
        }
        return render(
            request, "aois/admin/import_geojson.html", context=context
        )
