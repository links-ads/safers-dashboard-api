from rest_framework import generics
from rest_framework import permissions

from safers.users.models import Organization
from safers.users.serializers import OrganizationSerializer


class OrganizationView(generics.ListAPIView):

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = Organization.objects.active()
    serializer_class = OrganizationSerializer
