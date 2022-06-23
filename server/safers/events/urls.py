from django.urls import include, path, re_path

from rest_framework import routers

from safers.events.views import (EventViewSet)

api_router = routers.DefaultRouter()
api_router.register("events", EventViewSet, basename="events")
api_urlpatterns = [
    path("", include(api_router.urls)),
]

urlpatterns = []
