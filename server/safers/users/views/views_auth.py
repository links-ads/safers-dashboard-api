from collections import OrderedDict

from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.response import Response

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from allauth.account.models import EmailAddress

from dj_rest_auth.views import (
    LoginView as DjRestAuthLoginView,
    LogoutView as DjRestAuthLogoutView,
    PasswordChangeView as DjRestAuthPasswordChangeView,
    PasswordResetConfirmView as DjRestAuthPasswordResetConfirmView,
    PasswordResetView as DjRestAuthPasswordResetView,
    # UserDetailsView as DjRestAuthUserDetailsView,
)

from dj_rest_auth.registration.views import (
    RegisterView as DjRestAuthRegisterView,
    VerifyEmailView as DjRestAuthVerifyEmailView,
    ResendEmailVerificationView as DjRestAuthResendEmailVerificationView,
)

from safers.users.serializers import JWTSerializer

###################
# swagger schemas #
###################

_login_request_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties=OrderedDict((
        ("email", openapi.Schema(type=openapi.TYPE_STRING, example="admin@astrosat.net")),
        ("password", openapi.Schema(type=openapi.TYPE_STRING, example="password")),
    )),
)  # yapf: disable


_password_reset_request_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties=OrderedDict((
        ("email", openapi.Schema(type=openapi.TYPE_STRING, example="admin@astrosat.net")),
    )),
)  # yapf: disable

_resend_email_request_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties=OrderedDict((
        ("email", openapi.Schema(type=openapi.TYPE_STRING, example="admin@astrosat.net")),
    )),
)  # yapf: disable


_detail_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties=OrderedDict((
        ("detail", openapi.Schema(type=openapi.TYPE_STRING)),
    )),
)  # yapf: disable

#########
# views #
#########

# Very little is overwritten here; These views are
# sub-classed mostly just to add swagger documentation


@method_decorator(
    swagger_auto_schema(
        request_body=_login_request_schema,
        responses={status.HTTP_200_OK: JWTSerializer},
    ),
    name="post",
)
class LoginView(DjRestAuthLoginView):
    """
    Check the credentials and return the REST Token if the credentials are valid and authenticated.
    """
    pass


@method_decorator(
    swagger_auto_schema(auto_schema=None),
    name="get",
)
class LogoutView(DjRestAuthLogoutView):
    pass


class PasswordChangeView(DjRestAuthPasswordChangeView):
    pass


@method_decorator(
    swagger_auto_schema(
        request_body=_password_reset_request_schema,
        responses={status.HTTP_200_OK: _detail_schema},
    ),
    name="post",
)
class PasswordResetView(DjRestAuthPasswordResetView):
    pass


class PasswordResetConfirmView(DjRestAuthPasswordResetConfirmView):
    pass


class RegisterView(DjRestAuthRegisterView):
    pass


class VerifyEmailView(DjRestAuthVerifyEmailView):
    pass


@method_decorator(
    swagger_auto_schema(
        request_body=_resend_email_request_schema,
        responses={status.HTTP_200_OK: _detail_schema},
    ),
    name="post",
)
class ResendEmailVerificationView(DjRestAuthResendEmailVerificationView):
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = EmailAddress.objects.filter(**serializer.validated_data).first()
        if email and not email.verified:
            email.send_confirmation(request)
        else:
            # TODO: DO I WANT TO RETURN SOMETHING DIFFERENT IF A USER TRIES TO RESENT AN ALREADY VERIFIED EMAIL?
            pass

        return Response({'detail': _('ok')}, status=status.HTTP_200_OK)