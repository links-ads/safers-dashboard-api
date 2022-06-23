from django.urls import include, path, re_path

from rest_framework import routers

from safers.cameras.views import (
    CameraViewSet,
    CameraMediaViewSet,
    camera_media_sources_view,
)

api_router = routers.DefaultRouter()
api_router.register(
    "cameras/media", CameraMediaViewSet, basename="cameras_media"
)  # (order is important, lest DRF try to match "media" to "camera_id")
api_router.register("cameras", CameraViewSet, basename="cameras")
api_urlpatterns = [
    path(
        "cameras/media/sources",
        camera_media_sources_view,
        name="cameras_media-sources-list"
    ),
    path("", include(api_router.urls)),
]

urlpatterns = []
