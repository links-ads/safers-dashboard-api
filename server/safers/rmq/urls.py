from django.urls import include, path

from rest_framework import routers

from safers.rmq.views import MessageViewSet

api_router = routers.DefaultRouter()
api_router.register("messages", MessageViewSet, basename="messages")
api_urlpatterns = [
    path("", include(api_router.urls)),
    # path(
    #     "messages/publish",
    #     PublishMessageView.as_view(),
    #     name="messages-publish"
    # ),
]

urlpatterns = []
