from django.contrib.gis.geos import Polygon
from django.db.models import Q

from rest_framework.exceptions import ParseError

from rest_framework_gis.filterset import GeoFilterSet

from django_filters import rest_framework as filters


class CharInFilter(filters.BaseInFilter, filters.CharFilter):
    """
    Allows me to filter based on CharFields being in a list
    """

    pass


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
