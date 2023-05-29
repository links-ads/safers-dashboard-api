import logging

from django.conf import settings
from django.contrib.auth import logout
from django.db import transaction
from django.utils import timezone

from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema, OpenApiExample

from safers.users.models import User, UserStatus, ProfileDirection

from safers.auth.clients import AUTH_CLIENT
from safers.auth.permissions import AllowRegistrationPermission, AllowLoginPermission
from safers.auth.serializers import (
    RegisterViewSerializer,
    AuthenticateViewSerializer,
    RefreshViewSerializer,
    TokenSerializer,
)
from safers.auth.signals import user_registered_signal
from safers.auth.utils import reshape_auth_errors

logger = logging.getLogger(__name__)


class RegisterView(GenericAPIView):
    """
    Registers a user w/ FusionAuth.  Creates a corresponding local
    dashboard user.  Updates the corresponding remote gateway user.
    """
    permission_classes = [AllowRegistrationPermission]
    serializer_class = RegisterViewSerializer

    @transaction.atomic
    @extend_schema(
        request=RegisterViewSerializer,
        responses={status.HTTP_201_CREATED: None},
        examples=[
            OpenApiExample(
                "valid request",
                {
                    "email": "user@example.com",
                    "password": "RandomPassword123",
                    "first_name": "Test",
                    "last_name": "User",
                    "organization": "Test Organization",
                    "role": "organization_manager",
                    "accepted_terms": True,
                }
            )
        ]
    )
    def post(self, request, *args, **kwargs):
        # validate request parameters...
        serializer = self.get_serializer(
            data=request.data,
            context={
                # copy email to username
                "username": request.data.get("email"),
            }
        )
        serializer.is_valid(raise_exception=True)

        organization = serializer.validated_data.pop("organization", None)
        team = None  # TODO: CANNOT SET TEAM IN DASHBOARD YET
        role = serializer.validated_data.pop("role", None)
        accepted_terms = serializer.validated_data.pop("accepted_terms", False)

        # register w/ FusionAuth...
        auth_response = AUTH_CLIENT.register({
            "registration": {
                "applicationId": settings.FUSIONAUTH_APPLICATION_ID,
                "roles": [role.name],
            },
            "user": serializer.validated_data,
        })
        if not auth_response.was_successful():
            errors = reshape_auth_errors(auth_response.error_response)
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)
        auth_user_data = auth_response.success_response["user"]
        auth_token = auth_response.success_response["token"]

        # create local user...
        user = User.objects.create(
            auth_id=auth_user_data["id"],
            organization_name=organization.name if organization else None,
            role_name=role.name if role else None,
            email=auth_user_data["email"],
            username=auth_user_data["username"],
            accepted_terms=accepted_terms,
        )

        # update remote user...
        try:
            user.synchronize_profile(
                auth_token, ProfileDirection.REMOTE_TO_LOCAL
            )
            user.synchronize_profile(
                auth_token, ProfileDirection.LOCAL_TO_REMOTE
            )
            user.save()
        except Exception as exception:
            raise APIException(exception.message) from exception

        # signal the registration...
        user_registered_signal.send(
            None,
            instance=user,
            request=request,
        )

        return Response(status=status.HTTP_201_CREATED)


class AuthenticateView(GenericAPIView):
    """
    The 2nd part of the "authorization code grant".  Takes an authorization
    code from FusionAuth and returns an access_token for safers-dashboard.
    Creates/updates a local user as needed.
    """
    authentication_classes = []
    permission_classes = [AllowLoginPermission]
    serializer_class = AuthenticateViewSerializer

    @extend_schema(
        request=AuthenticateViewSerializer,
        responses={status.HTTP_200_OK: TokenSerializer},
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # TODO: MODIFY THIS TO COPE W/ SWAGGER ?
        redirect_uri = settings.FUSIONAUTH_REDIRECT_URL

        # get token...
        auth_token_response = AUTH_CLIENT.exchange_o_auth_code_for_access_token(
            code=serializer.validated_data["code"],
            redirect_uri=redirect_uri,
            client_id=settings.FUSIONAUTH_CLIENT_ID,
            client_secret=settings.FUSIONAUTH_CLIENT_SECRET,
        )
        if not auth_token_response.was_successful():
            errors = reshape_auth_errors(auth_token_response.error_response)
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)
        auth_token_data = auth_token_response.success_response

        # use token to get user details...
        auth_user_response = AUTH_CLIENT.retrieve_user(
            auth_token_data["userId"]
        )
        if not auth_user_response.was_successful():
            errors = reshape_auth_errors(auth_user_response.error_response)
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)
        auth_user_data = auth_user_response.success_response["user"]

        # get/create the corresponding local user...
        user, created = User.objects.get_or_create(
            auth_id=auth_token_data["userId"],
            defaults={
                "email": auth_user_data["email"],
                "username": auth_user_data["username"],
            }
        )

        # update user as needed...
        if user.status == UserStatus.PENDING:
            if created:
                # user was not yet created in the dashboard...
                # (therefore get remote details and save locally)
                user.synchronize_profile(
                    auth_token_data["access_token"],
                    ProfileDirection.REMOTE_TO_LOCAL
                )
            else:

                # user was already created in the dashboard...
                # (therefore get local details and save remotely)
                # TODO: MAY NOT NEED TO DO THIS B/C I'VE ALREADY DONE IT IN RegisterView
                user.synchronize_profile(
                    auth_token_data["access_token"],
                    ProfileDirection.LOCAL_TO_REMOTE
                )
            user.status = UserStatus.COMPLETED

        user.last_login = timezone.now()
        user.save()

        # check if the user satisfies all the login requirements...
        # (such as is_active, accepted_terms, etc.)
        # TODO: ...

        token_serializer = TokenSerializer(
            data=dict(user_id=user.id, **auth_token_data)
        )
        token_serializer.is_valid(raise_exception=True)
        token_serializer.save()

        logger.info(token_serializer.validated_data)

        return Response(
            token_serializer.validated_data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )


class RefreshView(GenericAPIView):

    serializer_class = RefreshViewSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        # TODO: MAYBE ADD REFRESH_TOKEN TO CONTEXT ?
        # context["refresh_token"] = ? BUT IF USER IS DOING THIS THEY CANNOT BE AUTHENTICATED
        return context

    @extend_schema(
        request=RefreshViewSerializer,
        responses={status.HTTP_200_OK: TokenSerializer},
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        auth_token_response = AUTH_CLIENT.exchange_refresh_token_for_access_token(
            refresh_token=serializer.validated_data["refresh_token"],
            client_id=settings.FUSIONAUTH_CLIENT_ID,
            client_secret=settings.FUSION_AUTH_CLIENT_SECRET,
        )
        if not auth_token_response.was_successful():
            errors = reshape_auth_errors(auth_token_response.error_response)
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)
        auth_token_data = auth_token_response.success_response

        user = User.objects.get(auth_id=auth_token_data["userId"])
        user.refresh_tokens.filter(
            token=serializer.validated_data["refresh_token"]
        ).delete()

        token_serializer = TokenSerializer(
            data=dict(user_id=user.id, **auth_token_data)
        )
        token_serializer.is_valid(raise_exception=True)
        token_serializer.save()

        logger.info(token_serializer.validated_data)

        return Response(
            token_serializer.validated_data, status=status.HTTP_200_OK
        )


class LogoutView(GenericAPIView):
    """
    Logout user locally from the dashboard by deleting all authentication
    tokens.  The user must still be logged out via FusionAuth, and any
    relevant state should still be deleted from the dashboard client.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=None,
        responses={status.HTTP_200_OK: None},
    )
    def post(self, request, *args, **kwargs):
        user = request.user
        # TODO: NEED TO BE A BIT MORE JUDICIOUS W/ WHAT GETS DELETED
        user.access_tokens.all().delete()
        user.refresh_tokens.all().delete()
        logout(request)

        logger.info(f"user '{user}' logged out.")

        return Response(status=status.HTTP_200_OK)
