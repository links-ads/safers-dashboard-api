from django.urls import include, path, re_path

from rest_framework import routers

from .views import (
    settings_view,
    trigger_error,
    DocumentView,
)

api_router = routers.DefaultRouter()
api_urlpatterns = [
    path("", include(api_router.urls)),
    # TODO: REFACTOR FRONTEND IN ORDER TO CHANGE PATH TO "settings"
    path("config", settings_view, name="settings"),
    path("sentry-debug", trigger_error, name="sentry-debug"),
    path(
        "documents/<slug:document_slug>",
        DocumentView.as_view(),
        name="documents"
    ),
]

urlpatterns = []
