from django.conf import settings
from django.contrib import admin, messages
from django.core.validators import FileExtensionValidator
from django.db import transaction
from django.db.models import JSONField
from django.forms import Form, FileField
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import path, reverse

import json
import numpy as np
import pandas as pd

from safers.core.admin import JSONAdminWidget

from safers.data.models import DataType


@admin.register(DataType)
class DataTypeAdmin(admin.ModelAdmin):
    change_list_template = "data/admin/datatype_changelist.html"
    fields = (
        "id",
        "datatype_id",
        "is_active",
        "description",
        "info",
        "group",
        "subgroup",
        "format",
        "source",
        "extra_info",
    )
    formfield_overrides = {
        JSONField: {
            "widget": JSONAdminWidget
        },
    }
    list_display = (
        "datatype_id",
        "group",
        "subgroup",
        "get_description_for_list_display",
    )
    list_filter = (
        "group",
        "subgroup",
        ("group", admin.EmptyFieldListFilter),
        ("subgroup", admin.EmptyFieldListFilter),
        "source",
    )
    readonly_fields = ("id", )
    search_fields = (
        "datatype_id",
        "group",
        "subgroup",
    )

    @admin.display(description="DESCRIPTION")
    def get_description_for_list_display(self, obj):
        description = obj.description
        if description:
            MAX_LEN = 20
            return description[:MAX_LEN] + "..." \
                if len(description) > MAX_LEN else description

    @property
    def url_basename(self):
        return self.model._meta.db_table

    def get_urls(self):
        urls = [
            path(
                "import-csv/",
                self.import_csv,
                name=f"{self.url_basename}_import_csv",
            )
        ] + super().get_urls()  # (order is important)
        return urls

    @admin.display(description="Import DataTypes from CSV")
    def import_csv(self, request):

        DATATYPE_COLUMNS = {
            "datatypeID": "datatype_id",
            "Group": "group",
            "Subgroup": "subgroup",
            "Format": "format",
            "Data Description": "description",
            "Info (short description )for frontend": "info",
            # "Responsible":
            # "Update frequency": "update_frequency",
            # "Comments":
            # "Data example":
            # "Style":
        }

        class ImportForm(Form):
            file = FileField(
                required=True,
                label="CSV File to Import",
                validators=[FileExtensionValidator(["csv"])]
            )

        if request.method == "GET":
            import_form = ImportForm()
        else:
            import_form = ImportForm(request.POST, request.FILES)

        if "apply" in request.POST:

            if import_form.is_valid():
                import_file = import_form.cleaned_data["file"]
                try:
                    df = pd.read_csv(import_file)
                    assert set(DATATYPE_COLUMNS).issubset(df.columns), "Invalid columns"
                    df = df.rename(columns=DATATYPE_COLUMNS)
                    df = df.replace({np.NaN: None})
                    with transaction.atomic():
                        n_created = n_updated = 0
                        for index, row in df.iterrows():
                            data_type, created = DataType.objects.get_or_create(datatype_id=row.datatype_id, subgroup=row.subgroup, group=row.group)
                            for field in DATATYPE_COLUMNS.values():
                                setattr(data_type, field, row[field])
                            data_type.extra_info = json.loads(row.to_json())
                            data_type.save()
                            if created:
                                n_created += 1
                            else:
                                n_updated += 1

                    self.message_user(
                        request,
                        f"successfully created {n_created} and updated {n_updated} models",
                        messages.SUCCESS,
                    )

                    changelist_url = reverse(
                        f"admin:{self.url_basename}_changelist"
                    )
                    return HttpResponseRedirect(changelist_url)

                except Exception as e:
                    self.message_user(request, str(e), messages.ERROR)

        context = {
            "form": import_form,
            "site_header": getattr(settings, "ADMIN_SITE_HEADER", None),
            "site_title": getattr(settings, "ADMIN_SITE_TITLE", None),
            "index_title": getattr(settings, "ADMIN_INDEX_TITLE", None),
        }
        return render(request, "core/admin/import.html", context=context)
