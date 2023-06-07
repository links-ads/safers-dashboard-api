from rest_framework.exceptions import APIException
from rest_framework.generics import ListAPIView

from rest_framework.permissions import IsAuthenticatedOrReadOnly

from safers.core.decorators import swagger_fake

from safers.users.models import Role
from safers.users.serializers import RoleSerializer


class RoleView(ListAPIView):
    """
    Returns all roles available from safers-gateway; These aren't
    true Django Models.  They are not persisted in the datbase.  Instead,
    they are retrieved via the safers-gateway API and cached as needed.  See
    safers.users.models.models_roles.RoleManager form ore info.
    """

    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = RoleSerializer

    @swagger_fake(None)
    def get_queryset(self):
        """
        Using the get_queryset method instead of the queryset attribute.  This
        provides graceful error handling when accessing safers-gateway.  It also 
        prevents that API from being accessed during swagger schema generation;
        Instead the swagger_fake decorator intenrcepts this call.
        """
        try:
            queryset = Role.objects.all()
            return queryset
        except Exception as exception:
            raise APIException(exception) from exception