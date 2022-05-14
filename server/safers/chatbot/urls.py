from django.urls import include, path, re_path

from rest_framework import routers

from safers.chatbot.views import (
    ReportView,
)

api_router = routers.DefaultRouter()
api_urlpatterns = [
    path("", include(api_router.urls)),
    path("chatbot/reports", ReportView.as_view(), name="reports-list"),
]

urlpatterns = []
