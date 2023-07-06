from django.conf import settings
from django.contrib import admin, messages
from django.core.validators import FileExtensionValidator
from django.db import transaction, IntegrityError
from django.db.models import JSONField
from django.forms import Form, FileField
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import path, reverse
from django.utils.html import mark_safe

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
        "group_info",
        "group",
        "subgroup",
        "format",
        "source",
        "domain",
        "feature_string",
        "opacity",
        "is_on_demand",
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
        "is_on_demand",
        "get_description_for_list_display",
    )
    list_filter = (
        "group",
        "subgroup",
        ("group", admin.EmptyFieldListFilter),
        ("subgroup", admin.EmptyFieldListFilter),
        "source",
        "domain",
        "is_on_demand",
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
        """
        imports the SAFERS datamapping form into the db
        """

        DESCRIPTION = mark_safe(
            "Note that this will import all DataType <i>layers</i>.<br/>Actual <i>groups</i> and <i>subgroups</i> still have to be added manually."
        )

        DATATYPE_COLUMNS = {
            "datatypeID": "datatype_id",
            "Group": "group",
            "Subgroup": "subgroup",
            "Format": "format",
            "Data Description": "description",
            "Info (short description )for frontend": "info",
            "Responsible": "source",
            "Domain": "domain",
            "GetFeatureInfo Format": "feature_string",
            "Opacity": "opacity",
            # (this is a CSV column but not a DB field;
            #  it is used to determine whether to process a CSV row
            #  - and it is conveniently ignored by the DB.)
            "When available? [ETA]": "when_available",
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
                        for _, row in df.iterrows():
                            if row.when_available == "not available":
                                # ingore datatypes that are not available
                                continue
                            try:
                                data_type, created = DataType.objects.get_or_create(datatype_id=row.datatype_id, subgroup=row.subgroup, group=row.group)
                            except IntegrityError as e:
                                # since this is all wrapped in a transaction.atomic() block the fn will still fail
                                # but this will give some useful information about the (1st) failing row
                                self.message_user(
                                    request,
                                    f"unable to process DataType {row.datatype_id}: {e}",
                                    messages.WARNING,
                                )
                            for field in DATATYPE_COLUMNS.values():
                                setattr(data_type, field, row[field])
                            data_type.extra_info = json.loads(row.to_json())
                            if data_type.extra_info.get(
                                "Update frequency"
                            ) == "on demand":
                                data_type.is_on_demand = True
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
            "description": DESCRIPTION,
        }
        return render(request, "core/admin/import.html", context=context)
