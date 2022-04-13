from django.urls import include, path

from rest_framework import routers

from safers.data.views import DataLayerViewSet

api_router = routers.DefaultRouter()
api_router.register("data/layers", DataLayerViewSet, basename="data_layers")
api_urlpatterns = [
    path("", include(api_router.urls)),
]

urlpatterns = []
