from datetime import datetime, timedelta

from django.contrib.gis.geos import Polygon
from django.db.models import Q
from django.utils import timezone

from rest_framework.exceptions import ParseError

from rest_framework_gis.filterset import GeoFilterSet

from django_filters import rest_framework as filters


class CharInFilter(filters.BaseInFilter, filters.CharFilter):
    """
    Allows me to filter based on CharFields being in a list
    """

    pass


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
