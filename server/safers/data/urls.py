from django.urls import include, path

from rest_framework import routers

from safers.data.views import (
    DataLayerView,
    DataLayerMetadataView,
)

api_router = routers.DefaultRouter()
api_urlpatterns = [
    path("", include(api_router.urls)),
    path(
        "data/layers",
        DataLayerView.as_view(),
        name="data-layers-list",
    ),
    path(
        "data/layers/metadata/<slug:metadata_id>",
        DataLayerMetadataView.as_view(),
        name="data-layers-metadata-detail",
    ),
]

urlpatterns = []
