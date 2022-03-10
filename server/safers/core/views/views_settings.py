from rest_framework import generics
from rest_framework.permissions import AllowAny

from safers.core.decorators import swagger_fake
from safers.core.models import SafersSettings
from safers.core.serializers import SafersSettingsSerializer


class SafersSettingsView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    queryset = SafersSettings.objects.all()
    serializer_class = SafersSettingsSerializer

    @swagger_fake(None)
    def get_object(self):
        return SafersSettings.load()
