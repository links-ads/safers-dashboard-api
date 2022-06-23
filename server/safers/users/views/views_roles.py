from rest_framework import generics
from rest_framework import permissions

from safers.users.models import Role
from safers.users.serializers import RoleSerializer


class RoleView(generics.ListAPIView):

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = Role.objects.active()
    serializer_class = RoleSerializer
