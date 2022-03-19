from django.conf import settings
from django.utils.decorators import method_decorator

from rest_framework import generics
from rest_framework import mixins
from rest_framework import viewsets

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from safers.core.decorators import swagger_fake
from safers.core.views import CannotDeleteViewSet

from safers.cameras.models import Camera, CameraMedia
from safers.cameras.serializers import CameraSerializer, CameraMediaSerializer


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

    @swagger_fake(CameraMedia.objects.none())
    def get_queryset(self):
        user = self.request.user
        # TODO: GET ALL THE CAMERA MEDIAS THIS USER CAN ACCESS
        return CameraMedia.objects.all()
