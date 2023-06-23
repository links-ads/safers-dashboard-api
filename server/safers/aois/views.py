from rest_framework import permissions
from rest_framework import viewsets

from safers.aois.models import Aoi
from safers.aois.serializers import AoiSerializer


class AoiViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Returns active AOIs as GeoJSON objects
    """

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = Aoi.objects.active()
    serializer_class = AoiSerializer
    lookup_field = "id"
    lookup_url_kwarg = "aoi_id"
