from django.urls import include, path, re_path

from rest_framework import routers

from .views import (
    RegisterView,
    LoginView,
    AuthenticateView,
    UserView,
    DashboardView,
)

api_router = routers.DefaultRouter()
# api_router.register("users/(?P<user_id>[^/.]+)/aois", AoiViewSet, basename="aois")
api_urlpatterns = [
    path("", include(api_router.urls)),
    path("users/<slug:user_id>", UserView.as_view(), name="user"),
    path("auth/register", RegisterView.as_view(), name="register"),
    path("auth/login", LoginView.as_view(), name="register"),
    path("auth/authenticate", AuthenticateView.as_view(), name="authenticate"),
]

urlpatterns = [
    path('dashboard', DashboardView.as_view(), name='dashboard'),
]
