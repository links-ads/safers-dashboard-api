from django.conf import settings
from django.utils.decorators import method_decorator

from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from django_filters import rest_framework as filters

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from safers.core.decorators import swagger_fake
from safers.core.filters import BBoxFilterSetMixin
from safers.core.views import CannotDeleteViewSet

from safers.cameras.models import Camera, CameraMedia
from safers.cameras.serializers import CameraSerializer, CameraMediaSerializer


class CameraMediaFilterSet(BBoxFilterSetMixin, filters.FilterSet):
    class Meta:
        model = CameraMedia
        fields = {}

    geometry__bboverlaps = filters.Filter(method="filter_geometry")
    geometry__bbcontains = filters.Filter(method="filter_geometry")


class CameraViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Returns a GeoJSON FeatureCollection of all cameras
    """
    # permission_classes = [TODO: SOME KIND OF FACTORY FUNCTION HERE]
    serializer_class = CameraSerializer
    lookup_field = "id"
    lookup_url_kwarg = "camera_id"

    @swagger_fake(Camera.objects.none())
    def get_queryset(self):
        user = self.request.user
        # TODO: GET ALL THE CAMERAS THIS USER CAN ACCESS
        return Camera.objects.all()


# TODO: FILTERS BY TYPE & TAG ETC.
class CameraMediaViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet
):
    # permission_classes = [TODO: SOME KIND OF FACTORY FUNCTION HERE]
    serializer_class = CameraMediaSerializer
    lookup_field = "id"
    lookup_url_kwarg = "camera_media_id"

    filter_backends = (filters.DjangoFilterBackend, )
    filterset_class = CameraMediaFilterSet

    @swagger_fake(CameraMedia.objects.none())
    def get_queryset(self):
        user = self.request.user
        # TODO: GET ALL THE CAMERA MEDIAS THIS USER CAN ACCESS
        return CameraMedia.objects.all()

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
