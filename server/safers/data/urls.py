from django.urls import include, path

from rest_framework import routers

from safers.data.views import DataLayerListView

api_router = routers.DefaultRouter()
api_urlpatterns = [
    path("", include(api_router.urls)),
    path(
        "data/layers",
        DataLayerListView.as_view(),
        name="data-layers-list",
    ),
]

urlpatterns = []
