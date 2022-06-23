from collections import OrderedDict

from django.conf import settings

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from safers.core.models import SafersSettings
from safers.core.serializers import SafersSettingsSerializer

_config_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties=OrderedDict((
        ("commitSha", openapi.Schema(type=openapi.TYPE_STRING)),
        ("allow_registration", openapi.Schema(type=openapi.TYPE_BOOLEAN)),
        ("require_verification", openapi.Schema(type=openapi.TYPE_BOOLEAN)),
        ("require_terms_acceptance", openapi.Schema(type=openapi.TYPE_BOOLEAN)),
        ("polling_frequency", openapi.Schema(type=openapi.TYPE_NUMBER)),
        ("request_timeout", openapi.Schema(type=openapi.TYPE_NUMBER)),
        ("max_favorite_alerts", openapi.Schema(type=openapi.TYPE_INTEGER)),
        ("max_favorite_events", openapi.Schema(type=openapi.TYPE_INTEGER)),
    ))
)  # yapf: disable


@swagger_auto_schema(
    methods=["GET"], responses={status.HTTP_200_OK: _config_schema}
)
@permission_classes([AllowAny])
@api_view(["GET"])
def config_view(request):
    """
    Returns some information required by the client for initial configuration
    """

    data = SafersSettingsSerializer(SafersSettings.load()).data
    data.update({
        "commitSha": None,
    })

    return Response(data)