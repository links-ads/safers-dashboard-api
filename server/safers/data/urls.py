from django.urls import include, path

from rest_framework import routers

from safers.data.views import (
    DataLayerView,
    data_layer_domains_view,
    data_layer_sources_view,
    DataLayerMetadataView,
    MapRequestViewSet,
)

api_router = routers.DefaultRouter()
api_router.register(
    "data/maprequests", MapRequestViewSet, basename="map_requests"
)
api_urlpatterns = [
    path("", include(api_router.urls)),
    path(
        "data/layers",
        DataLayerView.as_view(),
        name="data-layers-list",
    ),
    path(
        "data/layers/domains",
        data_layer_domains_view,
        name="data-layers-domains-list"
    ),
    path(
        "data/layers/sources",
        data_layer_sources_view,
        name="data-layers-sources-list"
    ),
    path(
        "data/layers/metadata/<slug:metadata_id>",
        DataLayerMetadataView.as_view(),
        name="data-layers-metadata-detail",
    ),
]

urlpatterns = []
