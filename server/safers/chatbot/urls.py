from django.urls import include, path, re_path

from rest_framework import routers

from safers.chatbot.views import (
    ReportListView,
    ReportDetailView,
)

api_router = routers.DefaultRouter()
api_urlpatterns = [
    path("", include(api_router.urls)),
    path("chatbot/reports", ReportListView.as_view(), name="reports-list"),
    path(
        "chatbot/reports/<slug:report_id>",
        ReportDetailView.as_view(),
        name="reports-detail"
    ),
]

urlpatterns = []
