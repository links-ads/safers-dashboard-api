from urllib.parse import urljoin

from django.conf import settings
from django.contrib.gis import geos

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema

from safers.core.clients import GATEWAY_CLIENT

from safers.chatbot.models import Action, ActionActivityTypes, ActionStatusTypes
from safers.chatbot.serializers import ActionSerializer, ActionViewSerializer
from .views_base import ChatbotView, parse_none, parse_datetime


class ActionView(ChatbotView):

    view_serializer_class = ActionViewSerializer
    model_serializer_class = ActionSerializer


class ActionListView(ActionView):

    GATEWAY_URL_PATH = "/api/services/app/Actions/GetActions"

    # @swagger_auto_schema(
    #     query_serializer=ActionViewSerializer,
    #     responses={status.HTTP_200_OK: ActionSerializer},
    # )
    @extend_schema(responses={
        status.HTTP_200_OK: ActionSerializer,
    })
    def get(self, request, *args, **kwargs):

        proxy_data = self.get_proxy_list_data(
            request,
            proxy_url=urljoin(
                settings.SAFERS_GATEWAY_URL, self.GATEWAY_URL_PATH
            ),
        )

        actions = [
            Action(
                action_id=data["id"],
                username=data.get("displayName"),
                organization=data.get("organizationName"),
                activity=data.get("activityName"),
                status=data.get("status"),
                timestamp=parse_datetime(data["timestamp"]),
                geometry=geos.Point(data["longitude"], data["latitude"])
                if "longitude" in data and "latitude" in data else None,
            ) for data in proxy_data
        ]

        model_serializer = self.model_serializer_class(
            actions, context=self.get_serializer_context(), many=True
        )

        return Response(data=model_serializer.data, status=status.HTTP_200_OK)


# _action_activities_schema = openapi.Schema(
#     type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)
# )
#
#
# @swagger_auto_schema(
#     responses={status.HTTP_200_OK: _action_activities_schema}, method="get"
# )
@api_view(["GET"])
@permission_classes([AllowAny])
def action_activities_view(request):
    """
    Returns the list of possible Action activities.
    """
    return Response(
        sorted(ActionActivityTypes.values), status=status.HTTP_200_OK
    )


# _action_statuses_schema = openapi.Schema(
#     type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)
# )
#
#
# @swagger_auto_schema(
#     responses={status.HTTP_200_OK: _action_statuses_schema}, method="get"
# )
@api_view(["GET"])
@permission_classes([AllowAny])
def action_statuses_view(request):
    """
    Returns the list of possible Action statuses.
    """
    return Response(sorted(ActionStatusTypes.values), status=status.HTTP_200_OK)
