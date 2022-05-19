from copy import deepcopy
from datetime import datetime, timedelta

from django.contrib.gis.geos import Polygon
from django.db.models import Q
from django.utils import timezone

from rest_framework.exceptions import ParseError

from rest_framework_gis.filterset import GeoFilterSet

from django_filters import rest_framework as filters
from django_filters import fields as filters_fields

from drf_yasg import openapi
from drf_yasg.inspectors import CoreAPICompatInspector


class SwaggerFilterInspector(CoreAPICompatInspector):
    """
    Make sure that filter widgets are rendered nicely in swagger
    idea came from https://github.com/axnsan12/drf-yasg/issues/514
    """
    def get_filter_parameters(self, filter_backend):

        parameters = []

        for parameter, (field_name, filter_field) in zip(
            super().get_filter_parameters(filter_backend),
            filter_backend.get_filterset_class(self.view).base_filters.items()
        ):
            assert parameter.name == field_name, "Error mapping filter fields to swagger"

            filter_field_type = type(filter_field)

            if issubclass(filter_field_type, filters.BooleanFilter):
                parameter.type = openapi.TYPE_BOOLEAN
            elif issubclass(filter_field_type, filters.ModelChoiceFilter):
                model_qs = filter_field.extra.get("queryset")
                if model_qs:
                    parameter.enum = list(
                        model_qs.values_list(
                            filter_field.extra.get("to_field_name", "pk"),
                            flat=True
                        )
                    )
            elif issubclass(filter_field_type, filters.ChoiceFilter):
                parameter.enum = [
                    choice[0] for choice in filter_field.extra.get("choices")
                ]
            elif issubclass(filter_field_type, filters.DateFilter):
                parameter.format = openapi.FORMAT_DATE
            elif issubclass(filter_field_type, filters.DateTimeFilter):
                parameter.format = openapi.FORMAT_DATETIME
            # elif issubclass(
            #     filter_field_type, filters.IsoDateTimeFromToRangeFilter
            # ):
            #     after_parameter = deepcopy(parameter)
            #     after_parameter.name = f"{field_name}_after"
            #     parameters.append(after_parameter)
            #     before_parameter = deepcopy(parameter)
            #     before_parameter.name = f"{field_name}_before"
            #     parameters.append(before_parameter)

            parameters.append(parameter)

        return parameters


class CharInFilter(filters.BaseInFilter, filters.CharFilter):
    """
    Allows me to filter based on CharFields being in a list
    """

    pass


class CaseInsensitiveChoiceFilter(filters.ChoiceFilter):
    class _CaseInsensitiveChoiceField(filters_fields.ChoiceField):
        def valid_value(self, value):
            case_insensitive_value = str(value).lower()
            return super().valid_value(case_insensitive_value)

        def _set_choices(self, value):
            return super()._set_choices(value)

        def _get_case_insensitive_choices(self):
            choices = map(
                lambda x: (x[0].lower(), x[1]), super()._get_choices()
            )
            return choices

        choices = property(_get_case_insensitive_choices, _set_choices)

    field_class = _CaseInsensitiveChoiceField


class DefaultFilterBackend(filters.DjangoFilterBackend):
    """
    alternative way of providing default values to filters
    as per https://github.com/astrosat/safers-gateway/issues/45
    (since DefaultFilterSetMixin might not be the best idea)
    """
    @property
    def default_filterset_kwargs(self):
        raise NotImplementedError(
            "default_filterset_kwargs must be implemented"
        )

    def get_filterset_kwargs(self, request, queryset, view):
        self.view = view
        kwargs = super().get_filterset_kwargs(request, queryset, view)
        data = kwargs["data"].copy()
        data.update(self.default_filterset_kwargs)
        kwargs["data"] = data
        return kwargs


class DefaultFilterSetMixin():
    """
    allows me to provide "initial" values as defaults
    (might not be the best idea as per https://django-filter.readthedocs.io/en/stable/guide/tips.html#using-initial-values-as-defaults)
    used to ensure that a user gets artefacts relative to their AOI and 72 hours, unless they specify otherwise
    """
    @staticmethod
    def default_aoi_bbox(request):
        user = request.user
        aoi_bbox = user.default_aoi.geometry.extent
        return ",".join(map(str, aoi_bbox))

    @staticmethod
    def default_end_date(request):
        return timezone.now()

    @staticmethod
    def default_start_date(request):
        return timezone.now() - timedelta(days=3)

    def __init__(self, data=None, *args, **kwargs):
        if data is not None:
            data = data.copy()

            for name, f in self.base_filters.items():
                initial = f.extra.get('initial')

                if not data.get(name) and initial:
                    if callable(initial):
                        data[name] = initial(kwargs["request"])
                    else:
                        data[name] = initial

        super().__init__(data, *args, **kwargs)


class BBoxFilterSetMixin():
    """
    Allows me to filter results by geometry by spatial lookups against a BBox
    (https://docs.djangoproject.com/en/4.0/ref/contrib/gis/geoquerysets/#spatial-lookups)

    usage are:
      <domain>/api/alerts/?<field_name>__<lookup_expr>=-2.890854,52.683303,-1.13833,53.209580

    """

    # geometry_bboverlaps = filters.Filter(method="filter_geometry")
    # geometry_bbcontains = filters.Filter(method="filter_geometry")

    LOOKUP_EXPRS = ["bboverlaps", "bbcontains"]

    def filter_geometry(self, queryset, name, value):

        field_name, lookup_expr = name.split("__", 1)
        if lookup_expr not in self.LOOKUP_EXPRS:
            raise ParseError("Invalid lookup expression supplied.")

        try:
            p1x, p1y, p2x, p2y = (float(n) for n in value.split(","))
        except ValueError:
            raise ParseError("Invalid bbox string supplied.")
        filter_bbox = Polygon.from_bbox((p1x, p1y, p2x, p2y))

        return queryset.filter(Q(**{name: filter_bbox}))
