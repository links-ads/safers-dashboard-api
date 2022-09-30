from django.urls import include, path, re_path

from rest_framework import routers

from safers.notifications.views import (
    NotificationViewSet,
    notification_sources_view,
    notification_types_view,
    notification_scopes_restrictions_view,
)

api_router = routers.DefaultRouter()
api_router.register(
    "notifications", NotificationViewSet, basename="notifications"
)
api_urlpatterns = [
    path("", include(api_router.urls)),
    path(
        "notifications/sources",
        notification_sources_view,
        name="notification-sources-list"
    ),
    path(
        "notifications/types",
        notification_types_view,
        name="notification-types-list"
    ),
    path(
        "notifications/scopes-restrictions",
        notification_scopes_restrictions_view,
        name="notification-scopes-restrictions-list"
    ),
]

urlpatterns = []
