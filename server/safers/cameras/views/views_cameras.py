from copy import deepcopy

from django.contrib.gis.geos import Polygon
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _

from rest_framework import status, viewsets
from rest_framework.exceptions import ParseError
from rest_framework.permissions import IsAuthenticated

from django_filters import rest_framework as filters

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from safers.core.filters import DefaultFilterSetMixin, SwaggerFilterInspector

from safers.cameras.models import Camera
from safers.cameras.serializers import CameraListSerializer, CameraDetailSerializer

###########
# swagger #
###########

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

###########
# filters #
###########


class CameraFilterSet(DefaultFilterSetMixin, filters.FilterSet):
    class Meta:
        model = Camera
        fields = {}

    camera_id = filters.CharFilter()

    bbox = filters.Filter(
        method="bbox_method", help_text=_("xmin, ymin, xmax, ymax")
    )
    default_bbox = filters.BooleanFilter(
        initial=False,
        help_text=_(
            "If default_bbox is True and no bbox is provided the user's default_aoi bbox will be used; "
            "If default_bbox is False and no bbox is provided then no bbox filter will be passed to the API"
        )
    )

    def bbox_method(self, queryset, name, value):

        try:
            xmin, ymin, xmax, ymax = list(map(float, value.split(",")))
        except ValueError:
            raise ParseError("invalid bbox string supplied")
        bbox = Polygon.from_bbox((xmin, ymin, xmax, ymax))

        return queryset.filter(geometry__intersects=bbox)

    def filter_queryset(self, queryset):
        """
        As per the documentation, I am overriding this method in order to perform
        additional filtering to the queryset before it is cached
        """

        # update filters based on default fields

        updated_cleaned_data = deepcopy(self.form.cleaned_data)

        default_bbox = updated_cleaned_data.pop("default_bbox")
        if default_bbox and not updated_cleaned_data.get("bbox"):
            user = self.request.user
            bbox = user.default_aoi.geometry.extent
            updated_cleaned_data["bbox"] = ",".join(map(str, bbox))

        self.form.cleaned_data = updated_cleaned_data

        return super().filter_queryset(queryset)


#########
# views #
#########


@method_decorator(
    swagger_auto_schema(
        responses={status.HTTP_200_OK: _camera_list_schema},
        filter_inspectors=[SwaggerFilterInspector],
    ),
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

    filter_backends = (filters.DjangoFilterBackend, )
    filterset_class = CameraFilterSet

    lookup_field = "camera_id"
    lookup_url_kwarg = "camera_id"
    queryset = Camera.objects.active()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ["list"]:
            return CameraListSerializer
        else:
            return CameraDetailSerializer
