from django.utils.decorators import method_decorator

from rest_framework import generics, status
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from safers.core.decorators import swagger_fake

from safers.users.models import User
from safers.users.permissions import IsSelfOrAdmin
from safers.users.serializers import UserSerializerLite, UserSerializer, ReadOnlyUserSerializer
from safers.users.views import synchronize_profile, SynchronizeProfileDirection

###########
# swagger #
###########

_user_request_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
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
        "remote_profile_fields": []
    }
)

_user_response_schema = _user_request_schema

#########
# views #
#########


@method_decorator(
    swagger_auto_schema(
        responses={status.HTTP_200_OK: _user_response_schema},
    ),
    name="get",
)
@method_decorator(
    swagger_auto_schema(
        request_body=_user_request_schema,
        responses={status.HTTP_200_OK: _user_response_schema},
    ),
    name="put",
)
@method_decorator(
    swagger_auto_schema(
        request_body=_user_request_schema,
        responses={status.HTTP_200_OK: _user_response_schema},
    ),
    name="patch",
)
class UserView(generics.RetrieveUpdateDestroyAPIView):
    lookup_field = "id"
    lookup_url_kwarg = "user_id"
    # parser_classes = [
    #     MultiPartParser, FormParser
    # ]  # the client sends data as multipart/form data
    permission_classes = [IsAuthenticated, IsSelfOrAdmin]
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            # prevent updating _all_ User fields, since updating organization or role causes problems in API
            # (b/c this is not a ViewSet, I have to inspect the request methods rather than using ".action")
            return ReadOnlyUserSerializer
        return UserSerializer

    @swagger_fake(None)
    def get_object(self):
        if self.kwargs[self.lookup_url_kwarg].upper() == "CURRENT":
            return self.request.user
        return super().get_object()

    # TODO: GOING TO ALLOW USERS TO UPDATE PROFILE FIELDS FOR NOW
    # @swagger_fake({})
    # def get_serializer_context(self):
    #     # if this is a remote user, I want to prevent updating any
    #     # profile fields which come from the remote auth_user
    #     context = super().get_serializer_context()
    #     user = self.get_object()
    #     if user.is_remote:
    #         context["prevent_remote_profile_fields"] = {
    #             field: getattr(user.profile, field)
    #             for field in user.auth_user.profile_fields
    #         }
    #     return context

    def delete(self, request, *args, **kwargs):
        retval = super().delete(request, *args, **kwargs)
        # TODO: delete user from FusionAuth and logout
        return retval

    def perform_update(self, serializer):
        retval = super().perform_update(serializer)

        if "default_aoi" not in serializer.validated_data:

            user = self.get_object()

            if user.is_remote:
                try:
                    synchronize_profile(
                        user.profile,
                        SynchronizeProfileDirection.LOCAL_TO_REMOTE
                    )
                except Exception as e:
                    msg = "Unable to update profile fields on authentication server."
                    raise APIException(msg)

        return retval
