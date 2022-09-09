from django.urls import include, path, re_path

from rest_framework import routers

from safers.chatbot.views import (
    ActionListView,
    action_activities_view,
    action_statuses_view,
    CommunicationListView,
    MissionListView,
    mission_statuses_view,
    ReportListView,
    ReportDetailView,
    report_categories_view,
)

api_router = routers.DefaultRouter()
api_urlpatterns = [
    path("", include(api_router.urls)),
    path(
        "chatbot/people",
        ActionListView.as_view(),
        name="actions-list",
    ),
    path(
        "chatbot/people/activities",
        action_activities_view,
        name="action-activities-list",
    ),
    path(
        "chatbot/people/statuses",
        action_statuses_view,
        name="action-statuses-list",
    ),
    path(
        "chatbot/communications",
        CommunicationListView.as_view(),
        name="communications-list",
    ),
    path(
        "chatbot/missions",
        MissionListView.as_view(),
        name="missions-list",
    ),
    path(
        "chatbot/missions/statuses",
        mission_statuses_view,
        name="mission-statuses-list",
    ),
    path(
        "chatbot/reports",
        ReportListView.as_view(),
        name="reports-list",
    ),
    path(
        "chatbot/reports/categories",
        report_categories_view,
        name="report-categories-list",
    ),
    path(
        "chatbot/reports/<slug:report_id>",
        ReportDetailView.as_view(),
        name="reports-detail"
    ),
]

urlpatterns = []
