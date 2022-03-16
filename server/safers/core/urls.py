from django.urls import include, path, re_path

from rest_framework import routers

from .views import (
    config_view,
)

api_router = routers.DefaultRouter()
api_urlpatterns = [
    path("", include(api_router.urls)),
    path("config", config_view, name="config"),
]

urlpatterns = []
