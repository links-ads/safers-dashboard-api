from django.urls import path

from .views import (
    RegisterView,
    AuthenticateView,
    RefreshView,
    LogoutView,
)

api_urlpatterns = [
    path(
        "auth/register",
        RegisterView.as_view(),
        name="auth-register",
    ),
    path(
        "auth/authenticate",
        AuthenticateView.as_view(),
        name="auth-authenticate",
    ),
    path(
        "auth/refresh",
        RefreshView.as_view(),
        name="auth-refresh",
    ),
    path(
        "auth/logout",
        LogoutView.as_view(),
        name="auth-logout",
    ),
]

urlpatterns = []
