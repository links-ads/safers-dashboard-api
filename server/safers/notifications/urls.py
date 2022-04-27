from django.urls import include, path, re_path

from rest_framework import routers

from safers.notifications.views import (NotificationViewSet)

api_router = routers.DefaultRouter()
api_router.register(
    "notifications", NotificationViewSet, basename="notifications"
)
api_urlpatterns = [
    path("", include(api_router.urls)),
]

urlpatterns = []
