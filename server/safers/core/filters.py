from datetime import datetime, timedelta

from django.contrib.gis.geos import Polygon
from django.db.models import Q
from django.utils import timezone

from rest_framework.exceptions import ParseError

from django_filters import rest_framework as filters
from django_filters import fields as filters_fields


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


class MultiFieldOrderingFilter(filters.OrderingFilter):
    """
    An ordering filter that allows multiple "implicit" fields to be used along w/ the specified filter value
    (so that a pre-ordered qs doesn't get overwritten)
    """
    def __init__(self, *args, **kwargs):
        multi_fields = kwargs.pop("multi_fields", [])
        primary = kwargs.pop("primary", False)
        assert isinstance(multi_fields, list)
        super().__init__(*args, **kwargs)
        self.multi_fields = multi_fields
        self.primary = primary

    def filter(self, qs, value):
        value = value or []
        multi_value = value + self.multi_fields if self.primary else self.multi_fields + value
        return super().filter(qs, multi_value)


class DefaultFilterBackend(filters.DjangoFilterBackend):
    """
    alternative way of providing default values to filters
    as per https://github.com/astrosat/safers-dashboard-api/issues/45
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
