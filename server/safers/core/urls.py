from django.urls import include, path, re_path

from rest_framework import routers

from .views import SafersSettingsView


api_router = routers.DefaultRouter()
api_urlpatterns = [
    path("", include(api_router.urls)),
    #  path("config", ClientConfigView.as_view(), name="config"),
    path("settings", SafersSettingsView.as_view(), name="settings"),
]

urlpatterns = [ 
]
