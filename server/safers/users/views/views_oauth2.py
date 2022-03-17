from collections import OrderedDict

from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.signals import user_logged_in, user_logged_out
# from django.shortcuts import redirect
# from django.urls import resolve, reverse

from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from knox.auth import TokenAuthentication
from knox.models import AuthToken
from knox.settings import knox_settings
from knox.views import (
    LoginView as KnoxLoginView,
    LogoutView as KnoxLogoutView,
    LogoutAllView as KnoxLogoutAllView,
)

from safers.users.exceptions import AuthenticationException
from safers.users.models import User
from safers.users.serializers import AuthenticateSerializer, KnoxTokenSerializer
from safers.users.utils import AUTH_CLIENT, create_knox_token
"""
code to authenticate using OAUTH2
(SHOULD EVENTUALLY REPLACE dj-rest-auth, ETC. IN "views_auth.py")

1. client makes request to oauth2 provider to get code
2. that redirects back to client incuding code in GET
3. if code is in GET, client POSTS code to AuthenticateView
4. that gets user details and generates token for client
"""

AUTH_USER_FIELDS = [
    # fields from auth_user to duplicate in user
    "email",
    "username",
]


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

    def _get_auth_token(self, request, data):
        response = AUTH_CLIENT.exchange_o_auth_code_for_access_token(
            code=data["code"],
            client_id=settings.FUSION_AUTH_CLIENT_ID,
            # redirect_uri=request.build_absolute_uri(reverse("authenticate")),
            redirect_uri=f"{settings.CLIENT_HOST}/auth/sign-in",
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

            user, created = User.objects.get_or_create(
                auth_id=auth_token_data["userId"],
                defaults={
                    k: v
                    for k, v in auth_user_data.items() if k in AUTH_USER_FIELDS
                }
            )
            if created:
                # TODO: register user
                pass

            # any additional user checks ?

            user_logged_in.send(sender=User, request=request, user=user)

            token = create_knox_token(None, user, None)
            token_serializer = KnoxTokenSerializer(token)

            return Response(
                token_serializer.data,
                status=status.HTTP_201_CREATED
                if created else status.HTTP_200_OK
            )

        except Exception as e:
            raise AuthenticationException(e)


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