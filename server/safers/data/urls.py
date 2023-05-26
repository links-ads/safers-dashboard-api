from django.urls import include, path

from rest_framework import routers

from safers.data.views import (
    OperationalLayerView,
    operational_layer_domains_view,
    on_demand_layer_domains_view,
    MapRequestViewSet,
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
        OperationalLayerView.as_view(),
        name="operational-layers-list",
    ),
    path(
        "data/layers/domains",
        operational_layer_domains_view,
        name="operational-layers-domains-list",
    ),
    path(
        "data/maprequests/domains",
        on_demand_layer_domains_view,
        name="ondemand-layers-domains-list",
    ),
    path(
        "data/layers/metadata/<slug:metadata_id>",
        DataLayerMetadataView.as_view(),
        name="data-layers-metadata-detail",
    ),
]

urlpatterns = []
