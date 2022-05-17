from django.urls import include, path, re_path

from rest_framework import routers

from safers.social.views import (
    # SocialEventViewSet,
    # SocialEventDetailListView,
    # SocialEventDetailRetrieveView,
    TweetView,
)

api_router = routers.DefaultRouter()
api_urlpatterns = [
    path("", include(api_router.urls)),
    path("social/tweets", TweetView.as_view(), name="tweet-list"),
]

urlpatterns = []
