from django.conf import settings
from django.urls import include, path, re_path
from django.views.generic import TemplateView

from rest_framework import routers

from .views import (
    LoginView,
    LogoutView,
    PasswordChangeView,
    PasswordResetConfirmView,
    PasswordResetView,
    RegisterView,
    VerifyEmailView,
    ResendEmailVerificationView,
    UserView,
)

api_router = routers.DefaultRouter()
# api_router.register("users/(?P<user_id>[^/.]+)/aois", AoiViewSet, basename="aois")
api_urlpatterns = [
    path("", include(api_router.urls)),
    path("users/<slug:user_id>", UserView.as_view(), name="user"),
]

# redefining dj-rest-auth URLS here to use custom views...
api_urlpatterns += [
    re_path(
        r'^password-reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,32})/$',
        TemplateView.as_view(template_name="password_reset_confirm.html"),
        name='password_reset_confirm'
    ),
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
    # even though safers-gateway is a "pure" API, dj-rest-auth might
    # require django-allauth views to be reachable for certain fns
    path('accounts/', include('allauth.urls')),
]
