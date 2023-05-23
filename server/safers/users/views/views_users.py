from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from safers.core.decorators import swagger_fake

from safers.users.models import User
from safers.users.permissions import IsSelfOrAdmin
from safers.users.serializers import UserSerializer


class UserView(
    # generics.CreateAPIView,  # creating users is handled by auth RegisterView
    generics.RetrieveUpdateDestroyAPIView,
):
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
        if self.kwargs[self.lookup_url_kwarg].lower() == "current":
            return self.request.user
        return super().get_object()

    def delete(self, request, *args, **kwargs):
        retval = super().delete(request, *args, **kwargs)
        # TODO: (logout and) delete user from auth
        return retval

    def perform_update(self, serializer):
        retval = super().perform_update(serializer)
        # TODO: synchronize profile w/ auth
        return retval
