from django.urls import include, path, re_path

from rest_framework import routers


api_router = routers.DefaultRouter()
api_urlpatterns = [
    path("", include(api_router.urls)),
]

urlpatterns = [ 
]
