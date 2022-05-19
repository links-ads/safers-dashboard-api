from django.utils.decorators import method_decorator

from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from safers.cameras.models import Camera
from safers.cameras.serializers import CameraListSerializer, CameraDetailSerializer



_camera_list_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    example={
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [1, 2]
                },
                "properties": {
                    "id": "PCF_El_Perello_083",
                    "description": "name: El_Perello, model: reolink RLC-823A, owner: PCF, nation: Spain",
                    "direction": 83,
                    "altitude": 298,
                    "location": {
                        "longitude": 1,
                        "latitude": 2,
                    },
                    "last_update": "2022-05-18T09:28:56.361Z",
                },
            }
        ]
    }
)  # yapf: disable

_camera_detail_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    example={
        "id": "PCF_El_Perello_083",
        "description": "name: El_Perello, model: reolink RLC-823A, owner: PCF, nation: Spain",
        "direction": 83,
        "altitude": 298,
        "location": {
            "longitude": 1,
            "latitude": 2,
        },
        "geometry": {
            "type": "Point",
            "coordinates": [1, 2]
        },
        "last_update": "2022-05-18T09:28:56.361Z",
    }
)  # yapf: disable



@method_decorator(
    swagger_auto_schema(responses={status.HTTP_200_OK: _camera_list_schema}),
    name="list"
)
@method_decorator(
    swagger_auto_schema(responses={status.HTTP_200_OK: _camera_detail_schema}),
    name="retrieve"
)
class CameraViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Returns a GeoJSON FeatureCollection of all cameras
    """

    lookup_field = "camera_id"
    lookup_url_kwarg = "camera_id"
    permission_classes = [AllowAny]
    queryset = Camera.objects.active()

    def get_serializer_class(self):
        if self.action in ["list"]:
            return CameraListSerializer
        else:
            return CameraDetailSerializer
