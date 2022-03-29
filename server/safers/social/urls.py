from django.urls import include, path, re_path

from rest_framework import routers

from safers.social.views import (
    SocialEventViewSet,
    SocialEventDetailListView,
    SocialEventDetailRetrieveView,
)

api_router = routers.DefaultRouter()
api_router.register(
    "social/events", SocialEventViewSet, basename="social_events"
)
api_urlpatterns = [
    path("", include(api_router.urls)),
    path(
        "social/events/detail",
        SocialEventDetailListView.as_view(),
        name="social_events_detail-list"
    ),
    path(
        "social/events/<slug:external_id>/detail",
        SocialEventDetailRetrieveView.as_view(),
        name="social_events_detail-retrieve"
    ),
]

urlpatterns = []
