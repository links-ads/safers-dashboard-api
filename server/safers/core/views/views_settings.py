from rest_framework import generics

from safers.core.decorators import swagger_fake
from safers.core.models import SafersSettings
from safers.core.permissions import IsAuthenticatedOrAdmin
from safers.core.serializers import SafersSettingsSerializer


class SafersSettingsView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticatedOrAdmin]
    queryset = SafersSettings.objects.all()
    serializer_class = SafersSettingsSerializer

    @swagger_fake(None)
    def get_object(self):
        return SafersSettings.load()
