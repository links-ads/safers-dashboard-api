from django.urls import include, path, re_path

from rest_framework import routers

from .views import (
    RegisterView,
    UserView,
    # AoiViewSet,
)

api_router = routers.DefaultRouter()
# api_router.register("users/(?P<user_id>[^/.]+)/aois", AoiViewSet, basename="aois")
api_urlpatterns = [
    path("", include(api_router.urls)),
    path("users", UserView.as_view(), name="user"),
    path("auth/register", RegisterView.as_view(), name="register"),
]

urlpatterns = [ 
]

