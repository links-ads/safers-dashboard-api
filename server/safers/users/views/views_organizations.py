from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from safers.users.models import Organization
from safers.users.serializers import OrganizationSerializer


class OrganizationView(generics.ListAPIView):

    permission_classes = [IsAuthenticated]
    queryset = Organization.objects.active()
    serializer_class = OrganizationSerializer
