from django.urls import include, path, re_path

from rest_framework import routers

from safers.aois.views import (
    AoiViewSet,
)

api_router = routers.DefaultRouter()
api_router.register(r"aois", AoiViewSet, basename="aoi")

api_urlpatterns = [
    path("", include(api_router.urls)),
]

urlpatterns = []
