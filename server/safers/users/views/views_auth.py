from collections import OrderedDict

from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.response import Response

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from allauth.account.models import EmailAddress

from dj_rest_auth.models import get_token_model
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

from safers.users.models import Role, Organization
from safers.users.serializers import KnoxTokenSerializer, JWTSerializer, RegisterSerializer
from safers.users.utils import AUTH_CLIENT, create_token

#################
# swagger stuff #
#################

try:
    # try to use _real_ data for swagger documentation
    DEFAULT_ROLE_ID = "b2301aa6-a24b-4201-9a6d-a63e450acc96"
    sample_role = Role.objects.first()
    if sample_role:
        sample_role_id = str(sample_role.id)
    else:
        sample_role_id = DEFAULT_ROLE_ID
except:
    sample_role_id = DEFAULT_ROLE_ID

try:
    # try to use _real_ data for swagger documentation
    DEFAULT_ORGANIZATION_ID = "c26763ba-3595-4ecc-a63b-aaa2c21a9acc"
    sample_organization = Organization.objects.first()
    if sample_organization:
        sample_organization_id = str(sample_organization.id)
    else:
        sample_organization_id = DEFAULT_ORGANIZATION_ID
except:
    sample_organization_id = DEFAULT_ORGANIZATION_ID

_login_request_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties=OrderedDict((
        ("email", openapi.Schema(type=openapi.TYPE_STRING, example="admin@astrosat.net")),
        ("password", openapi.Schema(type=openapi.TYPE_STRING, example="password")),
    )),
)  # yapf: disable

_login_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties=OrderedDict((
        ("access_token", openapi.Schema(type=openapi.TYPE_STRING, example="3302a7228e258b43389ef76b561a3e73c256b1c3ed14a373d624676dfad3fe0a")),
        ("expiry", openapi.Schema(type=openapi.TYPE_STRING, example="2022-03-31T19:20:28.391781Z")),
        ("user", openapi.Schema(type=openapi.TYPE_OBJECT,
            example={
                "id": "a788996c-424b-4021-bec9-a963fd37a8f2",
                "email": "admin@astrosat.net",
                "accepted_terms": True,
                "is_verified": True,
                "last_login": "2022-03-31T08:55:16.377335Z",
                "is_local": True,
                "is_remote": False,
                "organization": "7791f5fa-bb0a-42da-8fea-8c81ab614ee4",
                "role": "a5ec15be-67bc-43d3-9c5d-049f788bf163",
                "default_aoi": 2,
                "first_name": "Miles",
                "last_name": "Dyson",
                "company": "Cyberdyne Systems",
                "address": "123 Main Street",
                "city": "Los Angeles",
                "country": "USA",
                "avatar": None,
                "remote_profile_fields": [],
            }
        ))
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

_register_request_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties=OrderedDict((
        ("email", openapi.Schema(type=openapi.TYPE_STRING, example="user@example.com")),
        ("first_name", openapi.Schema(type=openapi.TYPE_STRING)),
        ("last_name", openapi.Schema(type=openapi.TYPE_STRING)),
        ("password", openapi.Schema(type=openapi.TYPE_STRING, example="RandomPassword123")),
        ("role", openapi.Schema(type=openapi.TYPE_STRING, example=sample_role_id)),
        ("organization", openapi.Schema(type=openapi.TYPE_STRING, example=sample_organization_id)),
        ("accepted_terms", openapi.Schema(type=openapi.TYPE_BOOLEAN)),
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
        responses={status.HTTP_200_OK: _login_response_schema},
    ),
    name="post",
)
class LoginView(DjRestAuthLoginView):
    """
    Check the credentials and return the REST Token if the credentials are valid and authenticated.
    """
    def get_response(self):

        # just a few tweaks to work w/ KnoxToken
        serializer_class = self.get_response_serializer()
        data = {
            # (self.token is actually a @dataclass)
            "token": self.token,
            "user": self.user,
        }
        serializer = serializer_class(
            instance=data, context={'request': self.request}
        )

        return Response(serializer.data, status=status.HTTP_200_OK)


@method_decorator(
    swagger_auto_schema(auto_schema=None),
    name="get",
)
class LogoutView(DjRestAuthLogoutView):
    def logout(self, request):

        # first delete the remote user data, etc...
        if request.user.is_remote:
            AUTH_CLIENT.logout(_global=False)
            auth_user = request.user.auth_user
            auth_user.delete()

        # then delete local token...
        try:
            request.auth.delete()
        except Exception as e:
            pass

        # super() will do the rest...
        return super().logout(request)


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


@method_decorator(
    swagger_auto_schema(
        request_body=_register_request_schema,
        responses={status.HTTP_200_OK: _login_response_schema},
    ),
    name="post",
)
class RegisterView(DjRestAuthRegisterView):
    def get_response_data(self, user):
        # some more tweaks to work w/ knox
        token_model = get_token_model()
        user.auth_token = create_token(token_model, user, None)
        return super().get_response_data(user)


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
