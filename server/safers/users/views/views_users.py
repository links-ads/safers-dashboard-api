from django.utils.decorators import method_decorator

from rest_framework import generics, status
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from safers.core.decorators import swagger_fake

from safers.users.models import User
from safers.users.permissions import IsSelfOrAdmin
from safers.users.serializers import UserSerializerLite, UserSerializer
from safers.users.views import synchronize_profile

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
    serializer_class = UserSerializer

    @swagger_fake(None)
    def get_object(self):
        if self.kwargs[self.lookup_url_kwarg].upper() == "CURRENT":
            return self.request.user
        return super().get_object()

    @swagger_fake({})
    def get_serializer_context(self):
        # if this is a remote user, I want to prevent updating any
        # profile fields which come from the remote auth_user
        context = super().get_serializer_context()
        user = self.get_object()
        if user.is_remote:
            context["prevent_remote_profile_fields"] = {
                field: getattr(user.profile, field)
                for field in user.auth_user.profile_fields
            }
        return context

    def delete(self, request, *args, **kwargs):
        retval = super().delete(request, *args, **kwargs)
        # TODO: logout
        return retval

    def perform_update(self, serializer):

        if "default_aoi" not in serializer.validated_data:

            user = self.get_object()
            if user.is_remote:
                user_profile = user.profile

                first_name = serializer.validated_data.get("profile", {}
                                                          ).get("first_name")
                last_name = serializer.validated_data.get("profile",
                                                          {}).get("last_name")
                role = serializer.validated_data.get("role")
                organization = serializer.validated_data.get("organization")

                user_profile_data = {
                    "user": {
                        "id": str(user.auth_id),
                        "email": user.email,
                        "username": user.username,
                        "firstName": first_name,
                        "lastName": last_name,
                        "roles": [role.name] if role else []
                    },
                    "organizationId":
                        int(organization.organization_id)
                        if organization else None
                }
                try:
                    synchronize_profile(user_profile, user_profile_data)
                except Exception as e:
                    msg = "Unable to update profile fields on authentication server."
                    raise APIException(msg)

        return super().perform_update(serializer)
