from django.urls import include, path, re_path

from rest_framework import routers

from safers.tasks.views import (PublishMessageView)

api_router = routers.DefaultRouter()
api_urlpatterns = [
    path("", include(api_router.urls)),
    path(
        "tasks/messages/publish",
        PublishMessageView.as_view(),
        name="messages-publish"
    ),
]

urlpatterns = []
