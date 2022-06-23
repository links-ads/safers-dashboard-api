from collections import OrderedDict

import datetime
import json

from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib.admin import widgets as admin_widgets
from django.core.exceptions import ValidationError
from django.db.models import fields
from django.forms import widgets
from django.templatetags.static import StaticNode
from django.urls import resolve, reverse
from django.utils.html import format_html
from django.utils.text import slugify
from django.utils.timezone import make_aware

from django.utils.translation import gettext_lazy as _

####################
# list_display fns #
####################


def get_clickable_m2m_list_display(model_class, queryset):
    """
    Prints a pretty (clickable) representation of a m2m field for an Admin's `list_display`.
    Note that when using this it is recommended to call `prefetch_related` in the Admin's
    `get_queryset` fn in order to avoid the "n+1" problem.
    """
    admin_change_url_name = f"admin:{model_class._meta.db_table}_change"
    list_display = [
        f"<a href='{reverse(admin_change_url_name, args=[obj.id])}'>{str(obj)}</a>"
        for obj in queryset
    ]
    return format_html(", ".join(list_display))


def get_clickable_fk_list_display(obj):
    """
    Prints a pretty (clickable) representation of a fk field for an Admin's `list_display`.
    """
    model_class = type(obj)
    admin_change_url_name = f"admin:{model_class._meta.db_table}_change"
    list_display = f"<a href='{reverse(admin_change_url_name, args=[obj.pk])}'>{str(obj)}</a>"
    return format_html(list_display)


#################
# admin widgets #
#################


class JSONAdminWidget(widgets.Textarea):
    """
    renders JSON in a pretty (indented) way
    """
    def __init__(self, attrs=None):
        default_attrs = {
            # make things a bit bigger
            "cols": "80",
            "rows": "20",
            "class": "vLargeTextField",
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)

    def format_value(self, value):
        try:
            value = json.dumps(json.loads(value), indent=2, sort_keys=True)
        except Exception:
            pass
        return value


###########
# filters #
###########


class CharListFilter(admin.FieldListFilter):
    """
    Lets me filter a CharField.  This is useful if I want to search some fields
    separately from those specified by the ModelAdmin's `search_fields` argument.
    """

    template = 'core/admin/char_filter.html'

    def __init__(self, field, request, params, model, model_admin, field_path):

        self.lookup_kwarg = f"{field_path}__icontains"
        self.parameter_name = field_path

        # the super() method will popuplate self.used_parameters...
        super().__init__(field, request, params, model, model_admin, field_path)

    def expected_parameters(self):
        return [self.lookup_kwarg]

    def value(self):
        return self.used_parameters.get(self.lookup_kwarg)

    def choices(self, changelist):
        # this filter doesn't actually have multiple choices, but Django expects this fn to be an iterable
        yield {
            'selected': self.value() is not None,
            'lookup_kwarg': self.lookup_kwarg,
            'lookup_value': self.value(),
            'all_query_string': changelist.get_query_string(remove=self.expected_parameters()),
            'other_params': {
                k: v
                for (k, v) in changelist.params.items()
                if k != self.lookup_kwarg
            },
        }  # yapf: disable


class DateRangeListFilter(admin.FieldListFilter):
    """
    Lets me filter a DateField based on a range of dates.
    Uses a standard Django Form in the Admin Template to do this.
    """

    # basic idea came from: https://github.com/silentsokolov/django-admin-rangefilter/

    earliest_time = datetime.time(0, 0, 0, 0)
    latest_time = datetime.time(23, 59, 59, 999999)
    template = 'core/admin/date_range_filter.html'

    def __init__(self, field, request, params, model, model_admin, field_path):

        assert isinstance(
            field, fields.DateField
        ), f"'{field_path}' must be an instance of DateField in order to use DateRangeListFilter"

        self.lookup_kwarg_gte = f"{field_path}__gte"
        self.lookup_kwarg_lte = f"{field_path}__lte"

        super().__init__(field, request, params, model, model_admin, field_path)

        self.form = self.form_class(self.used_parameters or None)
        self.id = slugify(self.title)
        self.model_admin = model_admin

    def expected_parameters(self):
        return [self.lookup_kwarg_gte, self.lookup_kwarg_lte]

    def queryset(self, request, queryset):
        if self.form.is_valid():
            lookup_val_gte = self.form.cleaned_data[self.lookup_kwarg_gte]
            if lookup_val_gte:
                queryset = queryset.filter(
                    **{self.lookup_kwarg_gte: lookup_val_gte}
                )
            lookup_val_lte = self.form.cleaned_data[self.lookup_kwarg_lte]
            if lookup_val_lte:
                queryset = queryset.filter(
                    **{self.lookup_kwarg_lte: lookup_val_lte}
                )

        return queryset

    def choices(self, changelist):
        # I actually use the form itself to render choices; I use this (required)
        # fn just to provide a value for the JS code w/in the template to reference
        yield {
            "reset_query_string":
                changelist.get_query_string(
                    remove=[self.lookup_kwarg_gte, self.lookup_kwarg_lte]
                )
        }

    @property
    def form_class(self):

        fields = OrderedDict(
            ((
                field_name,
                forms.DateField(
                    initial=None,
                    label="",
                    localize=True,
                    required=False,
                    widget=admin_widgets.AdminDateWidget(
                        attrs={"placeholder": field_placeholder}
                    )
                )
            ) for field_name,
             field_placeholder in
             zip([self.lookup_kwarg_gte, self.lookup_kwarg_lte],
                 [_("From date"), _("To date")]))
        )

        FormClass = type(
            "DateRangeForm", (forms.BaseForm, ), {"base_fields": fields}
        )

        def _clean(obj):
            cleaned_data = super(FormClass, obj).clean()
            lookup_val_gte = cleaned_data.get(self.lookup_kwarg_gte)
            lookup_val_lte = cleaned_data.get(self.lookup_kwarg_lte)

            if settings.USE_TZ:
                if lookup_val_gte is not None:
                    cleaned_data[self.lookup_kwarg_gte] = make_aware(
                        datetime.datetime.combine(
                            lookup_val_gte, self.earliest_time
                        )
                    )
                if lookup_val_lte is not None:
                    cleaned_data[self.lookup_kwarg_lte] = make_aware(
                        datetime.datetime.combine(
                            lookup_val_lte, self.latest_time
                        )
                    )
            if lookup_val_gte is not None and lookup_val_lte is not None:
                if lookup_val_gte > lookup_val_lte:
                    raise ValidationError(
                        "From date must be greater than To date"
                    )

            return cleaned_data

        setattr(FormClass, "clean", _clean)

        FormClass.scripts = [
            # pre-computing the paths to the scripts required for the AdminDateWidget
            # b/c I load them dynamically in the template (so that they're not duplicated)
            StaticNode.handle_simple("admin/js/calendar.js"),
            StaticNode.handle_simple("admin/js/admin/DateTimeShortcuts.js")
        ]

        return FormClass


class IncludeExcludeListFilter(admin.SimpleListFilter):
    """
    Lets me filter the listview on multiple values at once
    """

    # basic idea came from: https://github.com/ctxis/django-admin-multiple-choice-list-filter

    include_empty_choice = True
    parameter_name = None
    template = 'core/admin/include_exclude_filter.html'
    title = None

    def __init__(self, request, params, model, model_admin):
        super().__init__(request, params, model, model_admin)
        self.lookup_kwarg = f"{self.parameter_name}__in"
        self.lookup_kwarg_isnull = f"{self.parameter_name}__isnull"
        _lookup_val = params.get(self.lookup_kwarg) or []
        _lookup_val_isnull = params.get(self.lookup_kwarg_isnull)
        self.lookup_val = _lookup_val.split(",") if _lookup_val else []
        self.lookup_val_isnull = _lookup_val_isnull == str(True)
        self.empty_value_display = model_admin.get_empty_value_display()

    def lookups(self, request, model_admin):
        raise NotImplementedError()

    def queryset(self, request, queryset):
        if self.lookup_val:
            queryset = queryset.filter(**{self.lookup_kwarg: self.lookup_val})
        if self.lookup_val_isnull:
            queryset = queryset.filter(
                **{self.lookup_kwarg_isnull: self.lookup_val_isnull}
            )
        return queryset

    def choices(self, changelist):
        def _get_query_string(include=None, exclude=None):
            # need to work on a copy so I don't change it for other lookup_choices in the generator below
            selections = self.lookup_val.copy()
            if include and include not in selections:
                selections.append(include)
            if exclude and exclude in selections:
                selections.remove(exclude)
            if selections:
                return changelist.get_query_string({
                    self.lookup_kwarg: ",".join(selections)
                })
            else:
                return changelist.get_query_string(remove=[self.lookup_kwarg])

        yield {
            'selected': self.lookup_val is None and not self.lookup_val_isnull,
            'query_string': changelist.get_query_string(remove=[self.lookup_kwarg, self.lookup_kwarg_isnull]),
            'display': _('Any'),
        }  # yapf: disable
        for lookup, val in self.lookup_choices:
            yield {
                'selected': str(lookup) in self.lookup_val,
                'query_string': changelist.get_query_string({self.lookup_kwarg: lookup}, [self.lookup_kwarg_isnull]),
                'include_query_string': _get_query_string(include=str(lookup)),
                'exclude_query_string': _get_query_string(exclude=str(lookup)),
                'display': val,
            }  # yapf: disable
        if self.include_empty_choice:
            yield {
                'selected': bool(self.lookup_val_isnull),
                'query_string': changelist.get_query_string({self.lookup_kwarg_isnull: True}, [self.lookup_kwarg]),
                'display': self.empty_value_display,
            }  # yapf: disable
