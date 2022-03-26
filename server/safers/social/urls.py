from django.urls import include, path, re_path

from rest_framework import routers

from safers.social.views import (TweetViewSet)

api_router = routers.DefaultRouter()
api_router.register("social/tweets", TweetViewSet, basename="tweets")
api_urlpatterns = [
    path("", include(api_router.urls)),
]

urlpatterns = []
