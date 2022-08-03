from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from drf_yasg.utils import swagger_auto_schema

from safers.core.models import SafersSettings
from safers.core.serializers import SafersSettingsSerializer


@swagger_auto_schema(
    methods=["GET"], responses={status.HTTP_200_OK: SafersSettingsSerializer}
)
@permission_classes([AllowAny])
@api_view(["GET"])
def config_view(request):
    """
    Returns some information required by the client for initial configuration
    """

    settings = SafersSettings.load()
    serializer = SafersSettingsSerializer(settings)

    return Response(serializer.data)
