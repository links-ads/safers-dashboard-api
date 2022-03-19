from django.urls import include, path, re_path

from rest_framework import routers

from safers.alerts.views import (AlertViewSet)

api_router = routers.DefaultRouter()
api_router.register("alerts", AlertViewSet, basename="alerts")
api_urlpatterns = [
    path("", include(api_router.urls)),
]

urlpatterns = []
