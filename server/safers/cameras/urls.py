from django.urls import include, path, re_path

from rest_framework import routers

from safers.cameras.views import (
    CameraViewSet,
    CameraMediaViewSet,
)

api_router = routers.DefaultRouter()
api_router.register(
    "cameras/media", CameraMediaViewSet, basename="cameras_media"
)  # (order is important, lest DRF try to match "media" to "camera_id")
api_router.register("cameras", CameraViewSet, basename="cameras")
api_urlpatterns = [
    path("", include(api_router.urls)),
]

urlpatterns = []
