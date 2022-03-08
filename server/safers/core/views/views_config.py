from collections import OrderedDict

from django.conf import settings

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


class ConfigView(APIView):

    # AppConfigView has no serializer to generate a swagger schema from
    # so I define one here just to make the generated documentation work
    _schema = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties=OrderedDict((
            ("commitSha", openapi.Schema(type=openapi.TYPE_STRING)),
        ))
    )  # yapf: disable

    permission_classes = [AllowAny]

    @swagger_auto_schema(responses={status.HTTP_200_OK: _schema})
    def get(self, request, format=None):
        """
        Returns some information required by the client for initial configuration
        """

        config = {"commitSha": None}

        return Response(config)
