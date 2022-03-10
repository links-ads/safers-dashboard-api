from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from safers.users.models import Role
from safers.users.serializers import RoleSerializer


class RoleView(generics.ListAPIView):

    permission_classes = [IsAuthenticated]
    queryset = Role.objects.active()
    serializer_class = RoleSerializer
