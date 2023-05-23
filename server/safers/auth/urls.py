from django.urls import path

from .views import (
    RegisterView,
    AuthenticateView,
    RefreshView,
    login_view,
    logout_view,
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
]

urlpatterns = [
    path("login", login_view, name="auth-login"),
    path("logout", logout_view, name="auth-logout"),
]