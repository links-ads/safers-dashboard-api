from datetime import datetime, timedelta

from django.conf import settings
from django.utils import timezone
from django.utils.decorators import method_decorator

from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from django_filters import rest_framework as filters

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from safers.core.decorators import swagger_fake
from safers.core.filters import BBoxFilterSetMixin, DefaultFilterSetMixin

from safers.users.permissions import IsLocal, IsRemote

from safers.cameras.models import Camera, CameraMedia
from safers.cameras.serializers import CameraListSerializer, CameraDetailSerializer, CameraMediaSerializer



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

class CameraMediaFilterSet(
    DefaultFilterSetMixin, BBoxFilterSetMixin, filters.FilterSet
):
    class Meta:
        model = CameraMedia
        fields = {}

    geometry__bboverlaps = filters.Filter(
        method="filter_geometry",
        # initial=DefaultFilterSetMixin.filter_on_default_aoi_bbox
    )
    date_range = filters.DateFromToRangeFilter(
        field_name="timestamp",
        # initial=DefaultFilterSetMixin.filter_on_default_date_range
    )


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


# TODO: FILTERS BY TYPE & TAG ETC.
class CameraMediaViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet
):
    # permission_classes = [TODO: SOME KIND OF FACTORY FUNCTION HERE]
    permission_classes = [IsAuthenticated]
    serializer_class = CameraMediaSerializer
    lookup_field = "id"
    lookup_url_kwarg = "camera_media_id"

    filter_backends = (filters.DjangoFilterBackend, )
    filterset_class = CameraMediaFilterSet

    @swagger_fake(CameraMedia.objects.none())
    def get_queryset(self):
        user = self.request.user
        queryset = CameraMedia.objects.all()

        if self.action != "favorite":
            # allow favoriting an object event if it's not w/in the default bbox / date_range
            query_params = self.request.query_params
            if "geometry__bboverlaps" not in query_params:
                queryset = queryset.overlaps(user.default_aoi.geometry)
            if "date_range" not in query_params:
                before_date = timezone.now()
                after_date = before_date - timedelta(days=3)
                queryset = queryset.date_range(before_date, after_date)

        return queryset

    @action(detail=True, methods=["post"])
    def favorite(self, request, **kwargs):
        """
        Toggles the favorite status of the specified object
        """
        user = request.user
        obj = self.get_object()

        if obj not in user.favorite_camera_medias.all():
            max_favorites = settings.SAFERS_MAX_FAVORITE_CAMERA_MEDIA
            if user.favorite_camera_medias.count() >= max_favorites:
                raise ValidationError(
                    f"cannot have more than {max_favorites} camera_media."
                )
            user.favorite_camera_medias.add(obj)
        else:
            user.favorite_camera_medias.remove(obj)

        SerializerClass = self.get_serializer_class()
        serializer = SerializerClass(obj, context=self.get_serializer_context())

        return Response(serializer.data, status=status.HTTP_200_OK)
