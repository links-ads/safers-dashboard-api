import re
from datetime import datetime
from urllib.parse import urljoin

from django.conf import settings
from django.contrib.gis import geos

from rest_framework import status
from rest_framework.response import Response

from drf_yasg.utils import swagger_auto_schema

from safers.chatbot.models import Action
from safers.chatbot.serializers import ActionSerializer, ActionViewSerializer
from .views_base import ChatbotView

# output of chatbot action timestamp is not standard
# this regex is used to throw away milliseconds and replace the timezone
ACTION_TIMESTAMP_REGEX = re.compile(r"^(.*)(\.\d+)(Z)")


class ActionView(ChatbotView):

    view_serializer_class = ActionViewSerializer
    model_serializer_class = ActionSerializer


class ActionListView(ActionView):

    GATEWAY_URL_PATH = "/api/services/app/Actions/GetActions"

    @swagger_auto_schema(
        query_serializer=ActionViewSerializer,
        responses={status.HTTP_200_OK: ActionSerializer},
    )
    def get(self, request, *args, **kwargs):

        proxy_data = self.get_proxy_list_data(
            request,
            proxy_url=urljoin(
                settings.SAFERS_GATEWAY_API_URL, self.GATEWAY_URL_PATH
            ),
        )

        actions = [
            Action(
                action_id=data["id"],
                username=data.get("displayName"),
                organization=data.get("organizationName"),
                activity=data.get("activityName"),
                status=data.get("status"),
                timestamp=datetime.fromisoformat(
                    ACTION_TIMESTAMP_REGEX.sub(r"\1+00:00", data["timestamp"])
                ),
                geometry=geos.Point(data["longitude"], data["latitude"])
                if "longitude" in data and "latitude" in data else None,
            ) for data in proxy_data
        ]

        model_serializer = self.model_serializer_class(
            actions, context=self.get_serializer_context(), many=True
        )

        return Response(data=model_serializer.data, status=status.HTTP_200_OK)
