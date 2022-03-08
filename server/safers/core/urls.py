from django.urls import include, path, re_path

from rest_framework import routers

from .views import (
    IndexView,
    ConfigView,
    SafersSettingsView,
)

api_router = routers.DefaultRouter()
api_urlpatterns = [
    path("", include(api_router.urls)),
    path("config", ConfigView.as_view(), name="config"),
    path("settings", SafersSettingsView.as_view(), name="settings"),
]

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
]
