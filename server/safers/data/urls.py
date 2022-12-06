from django.urls import include, path

from rest_framework import routers

from safers.data.views import (
    DataLayerView,
    data_layer_domains_view,
    MapRequestViewSet,
    map_request_domains_view,
    DataLayerMetadataView,
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
        "data/maprequests/domains",
        map_request_domains_view,
        name="map-requests-domains-list"
    ),
    path(
        "data/layers/metadata/<slug:metadata_id>",
        DataLayerMetadataView.as_view(),
        name="data-layers-metadata-detail",
    ),
]

urlpatterns = []
