from django.conf import settings
from django.urls import include, path, re_path
from django.views.generic import TemplateView

from rest_framework import routers

from .views import (
    Oath2LoginView,
    Oauth2LogoutView,
    Oauth2LogoutAllView,
    LoginView,
    LogoutView,
    PasswordChangeView,
    PasswordResetConfirmView,
    PasswordResetView,
    RegisterView,
    VerifyEmailView,
    ResendEmailVerificationView,
    OrganizationView,
    RoleView,
    UserView,
)

api_router = routers.DefaultRouter()
# TODO: AOI VIEWSET
api_urlpatterns = [
    path("", include(api_router.urls)),
    path("oauth2/login", Oath2LoginView.as_view(), name="oauth2-login"),
    path("oauth2/logout", Oauth2LogoutView.as_view(), name="oauth2-logout"),
    path(
        "oauth2/logoutall",
        Oauth2LogoutAllView.as_view(),
        name="oauth2-logoutall"
    ),
    path("users/<slug:user_id>", UserView.as_view(), name="users"),
    path("organizations/", OrganizationView.as_view(), name="organizations"),
    path("roles/", RoleView.as_view(), name="roles"),
]

# redefining dj-rest-auth URLS here to use custom views...
api_urlpatterns += [
    # not needed; password-reset comes from client
    # re_path(
    #     r'^password-reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,32})/$',
    #     TemplateView.as_view(template_name="password_reset_confirm.html"),
    #     name='password_reset_confirm'
    # ),
    path('auth/password/reset/', PasswordResetView.as_view(), name='rest_password_reset'),
    path('auth/password/reset/confirm/', PasswordResetConfirmView.as_view(), name='rest_password_reset_confirm'),
    path('auth/login/', LoginView.as_view(), name='rest_login'),
    path('auth/logout/', LogoutView.as_view(), name='rest_logout'),
    path('auth/password/change/', PasswordChangeView.as_view(), name='rest_password_change'),
    path('auth/register/', RegisterView.as_view(), name='rest_register'),
    path('auth/register/verify-email/', VerifyEmailView.as_view(), name='rest_verify_email'),
    path('auth/register/resend-email/', ResendEmailVerificationView.as_view(), name="rest_resend_email"),
    path('auth/register/account-email-verification-sent/', TemplateView.as_view(), name='account_email_verification_sent'),
    # TODO: OVERRIDE account-confirm-email TO USE CLIENT API
    re_path(r'^auth/register/account-confirm-email/(?P<key>[-:\w]+)/$', TemplateView.as_view(), name='account_confirm_email'),
]  # yapf: disable

if getattr(settings, 'REST_USE_JWT', False):
    from rest_framework_simplejwt.views import TokenVerifyView
    from dj_rest_auth.jwt_auth import get_refresh_view

    api_urlpatterns += [
        path(
            'auth/token/verify/',
            TokenVerifyView.as_view(),
            name='token_verify'
        ),
        path(
            'auth/token/refresh/',
            get_refresh_view().as_view(),
            name='token_refresh'
        ),
    ]

urlpatterns = [
    # even though safers-dashboard-api is a "pure" API, dj-rest-auth might
    # require django-allauth views to be reachable for certain fns
    path('accounts/', include('allauth.urls')),
]
