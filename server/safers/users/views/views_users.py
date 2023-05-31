from rest_framework import status, generics as drf_generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from safers.auth.clients import AUTH_CLIENT
from safers.auth.utils import reshape_auth_errors

from safers.core import generics as safers_generics
from safers.core.decorators import swagger_fake

from safers.users.models import User, ProfileDirection
from safers.users.permissions import IsSelf
from safers.users.serializers import UserSerializer


class UserView(
    # drf_generics.CreateAPIView,  # creating users is handled by auth RegisterView
    safers_generics.RetrievePatchlessUpdateDestroyAPIView
):

    lookup_field = "id"
    lookup_url_kwarg = "user_id"
    # parser_classes = [
    #     MultiPartParser, FormParser
    # ]  # the client sends data as multipart/form data
    permission_classes = [IsAuthenticated, IsSelf]
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @swagger_fake(None)
    def get_object(self):
        if self.kwargs[self.lookup_url_kwarg].lower() == "current":
            return self.request.user
        return super().get_object()

    def perform_update(self, serializer):
        """
        propagate profile changes to gateway 
        """
        user = serializer.save()
        auth_token = self.request.auth
        user.synchronize_profile(auth_token, ProfileDirection.LOCAL_TO_REMOTE)

    def perform_destroy(self, instance):
        """
        delete user from FusionAuth
        """
        auth_response = AUTH_CLIENT.delete_user(user_id=instance.auth_id)
        if not auth_response.was_successful():
            errors = reshape_auth_errors(auth_response.error_response)
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)
        instance.delete()
