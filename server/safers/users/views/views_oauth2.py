import json

from collections import OrderedDict
from sys import stdout

from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.templatetags.static import static

from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.utils.encoders import JSONEncoder

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from knox.settings import knox_settings
from knox.views import (
    LoginView as KnoxLoginView,
    LogoutView as KnoxLogoutView,
    LogoutAllView as KnoxLogoutAllView,
)

from safers.users.exceptions import AuthenticationException
from safers.users.models import User, Oauth2User, AUTH_USER_FIELDS, AUTH_PROFILE_FIELDS, AUTH_TOKEN_FIELDS
from safers.users.serializers import AuthenticateSerializer, Oauth2RegisterViewSerializer, KnoxTokenSerializer, UserSerializerLite, UserProfileSerializer
from safers.users.utils import AUTH_CLIENT, create_knox_token
"""
code to authenticate using OAUTH2
(SHOULD EVENTUALLY REPLACE dj-rest-auth, ETC. IN "views_auth.py")

1. client makes request to oauth2 provider to get code
2. that redirects back to client incuding code in GET
3. if code is in GET, client POSTS code to AuthenticateView
4. that gets user details and generates token for client
"""


class LoginView(GenericAPIView):
    """
    Part 2 of the authorization code flow;
    - the client redirects to the oauth2 provider and requests an authorization_code
    - upon success the oauth2 provider redirects to the client w/ the code in the URL
    - the client POSTS that code to this view
    - this view exchanges the code for an auth_token
    - it uses that auth_token to get/create a local user
    - it stores the auth_token and creates a local_token
    - it returns the local_token along w/ user details to the client
    """

    permission_classes = [AllowAny]
    serializer_class = AuthenticateSerializer

    @property
    def is_swagger(self):
        return "api/swagger" in self.request.headers.get("referer", "")

    def _get_auth_token(self, request, data):
        redirect_uri = request.build_absolute_uri(
            static("drf-yasg/swagger-ui-dist/oauth2-redirect.html")
        ) if self.is_swagger else f"{settings.CLIENT_HOST}/auth/sign-in"

        response = AUTH_CLIENT.exchange_o_auth_code_for_access_token(
            code=data["code"],
            client_id=settings.FUSION_AUTH_CLIENT_ID,
            # redirect_uri=request.build_absolute_uri(reverse("authenticate")),
            # redirect_uri=f"{settings.CLIENT_HOST}/auth/sign-in",
            redirect_uri=redirect_uri,
            client_secret=settings.FUSION_AUTH_CLIENT_SECRET,
        )
        if not response.was_successful():
            raise AuthenticationException(response.error_response)

        return response.success_response

    def _get_auth_user(self, request, data):
        response = AUTH_CLIENT.retrieve_user(data["userId"])
        if not response.was_successful():
            raise AuthenticationException(response.error_response)
        return response.success_response["user"]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties=OrderedDict(
                (("code", openapi.Schema(type=openapi.TYPE_STRING)), )
            ),
        ),
        responses={status.HTTP_200_OK: KnoxTokenSerializer},
    )
    def post(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            auth_token_data = self._get_auth_token(
                request,
                serializer.validated_data,
            )
            auth_user_data = self._get_auth_user(
                request,
                auth_token_data,
            )

            user, created_user = User.objects.get_or_create(
                auth_id=auth_token_data["userId"],
                defaults={
                    AUTH_USER_FIELDS[k]: v
                    for k, v in auth_user_data.items() if k in AUTH_USER_FIELDS
                }
            )
            if created_user:
                profile_serializer = UserProfileSerializer()
                profile_data = {
                    AUTH_PROFILE_FIELDS[k]: v
                    for k,
                    v in auth_user_data.items() if k in AUTH_PROFILE_FIELDS
                }
                profile_serializer.update(user.profile, profile_data)

                # TODO: register user extr steps ?
                pass

            # any additional user checks ?
            # user_logged_in.send(sender=User, request=request, user=user)

            auth_user, created_auth_user = Oauth2User.objects.get_or_create(user=user)
            auth_user.data = auth_user_data
            for k, v in auth_token_data.items():
                if k in AUTH_TOKEN_FIELDS:
                    setattr(auth_user, AUTH_TOKEN_FIELDS[k], v)
            auth_user.save()

            token_dataclass = create_knox_token(None, user, None)
            token_serializer = KnoxTokenSerializer(token_dataclass)

            if self.is_swagger:
                json.dump(
                    token_serializer.data, fp=stdout, indent=2, cls=JSONEncoder
                )

            return Response(
                token_serializer.data,
                status=status.HTTP_201_CREATED
                if created_user else status.HTTP_200_OK
            )

        except Exception as e:
            raise AuthenticationException(e)


_register_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    example={
        "email": "allyn.treshansky+1@astrosat.net",
        "first_name": "Allyn",
        "last_name": "Treshansky",
        "password": "RandomPassword123",
        "role": "Organization Manager",
        "organization": "Test Organization",
        "accepted_terms": True,
    }
)


# TODO: DEAL W/ ORGANIZATIONS & ROLES FROM FA
class RegisterView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = Oauth2RegisterViewSerializer

    @swagger_auto_schema(
        request_body=_register_schema,
        responses={status.HTTP_200_OK: UserSerializerLite},
    )
    def post(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        request_params = {
            "registration": {
                "applicationId": settings.FUSION_AUTH_CLIENT_ID,
            },
            "user": {
                "email": serializer.validated_data["email"],
                "username": serializer.validated_data["email"].strip("@")[0],
                "password": serializer.validated_data["password"],
                "firstName": serializer.validated_data["first_name"],
                "lastName": serializer.validated_data["last_name"],
                "twoFactorEnabled": False,
            },
        }
        response = AUTH_CLIENT.register(request_params)

        if not response.was_successful():
            # reshape the errors so the dashboard client can parse them
            # note that this won't map directly to the form (b/c the response
            # comes from FusionAuth and not the dashboard itself) - so these
            # messages will be rendered by the `getGeneralErrors` function
            exception_message = {
                field: [error.get("message") for error in errors]
                for field, errors in response.error_response.get("fieldErrors", {}).items()
            }  # yapf: disable
            raise APIException(exception_message)

        auth_user_data = response.success_response["user"]
        user, created_user = User.objects.get_or_create(
            auth_id=auth_user_data["id"],
            defaults=dict(
                organization=serializer.validated_data["organization"],
                role=serializer.validated_data["role"],
                **{
                    AUTH_USER_FIELDS[k]: v
                    for k, v in auth_user_data.items() if k in AUTH_USER_FIELDS
                }
            )
        )
        if created_user:
            profile_serializer = UserProfileSerializer()
            profile_data = {
                AUTH_PROFILE_FIELDS[k]: v
                for k,
                v in auth_user_data.items() if k in AUTH_PROFILE_FIELDS
            }
            profile_serializer.update(user.profile, profile_data)

        return Response(data=UserSerializerLite(user).data)


class LogoutView(KnoxLogoutView):
    @swagger_auto_schema(
        responses={status.HTTP_204_NO_CONTENT: None},
    )
    def post(self, request, **kwargs):
        user = request.user

        user_logged_out.send(sender=User, request=request, user=user)

        # first delete oauth2 token...
        # TODO

        # then delete knox token...
        super().post(request, **kwargs)


class LogoutAllView(KnoxLogoutAllView):
    @swagger_auto_schema(
        responses={status.HTTP_204_NO_CONTENT: None},
    )
    def post(self, request, **kwargs):
        user = request.user

        user_logged_out.send(sender=User, request=request, user=user)

        # first delete oauth2 token...
        # TODO

        # then delete all knox tokens...
        super().post(request, **kwargs)
