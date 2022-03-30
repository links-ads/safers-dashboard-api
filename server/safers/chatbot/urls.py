from django.urls import include, path, re_path

from rest_framework import routers

from safers.chatbot.views import (
    ReportViewSet,
)

api_router = routers.DefaultRouter()
api_router.register("chatbot/reports", ReportViewSet, basename="reports")
api_urlpatterns = [
    path("", include(api_router.urls)),
]

urlpatterns = []
