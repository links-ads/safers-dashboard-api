from django.utils.decorators import method_decorator

from rest_framework import permissions
from rest_framework import status
from rest_framework import viewsets

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from safers.aois.models import Aoi
from safers.aois.serializers import AoiSerializer

###########
# swagger #
###########

_geojson_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    example={
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [1, 2],
                        [3, 4],
                    ]
                },
                "properties": {
                    "id": 1,
                    "name": "string",
                    "description": "string",
                    "country": "string",
                    "zoomLevel": 0,
                    "midPoint": [1, 2]
                }
            }
        ]
    }
)  # yapf: disable

_geojson_list_schema = openapi.Schema(
    type=openapi.TYPE_ARRAY, items=_geojson_schema
)

#########
# views #
#########


@method_decorator(
    swagger_auto_schema(responses={status.HTTP_200_OK: _geojson_list_schema}),
    name="list",
)
@method_decorator(
    swagger_auto_schema(responses={status.HTTP_200_OK: _geojson_schema}),
    name="retrieve",
)
class AoiViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Returns all active AOIs as GeoJSON objects
    """

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = Aoi.objects.active()
    serializer_class = AoiSerializer
    lookup_field = "id"
    lookup_url_kwarg = "aoi_id"
