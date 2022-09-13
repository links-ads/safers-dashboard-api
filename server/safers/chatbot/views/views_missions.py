import json
import requests
from collections import OrderedDict
from urllib.parse import urljoin

from django.conf import settings
from django.contrib.gis import geos

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import APIException
from rest_framework.permissions import AllowAny
from rest_framework.utils.encoders import JSONEncoder
from rest_framework.response import Response

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from safers.users.authentication import ProxyAuthentication

from safers.chatbot.models import Mission, MissionStatusTypes
from safers.chatbot.serializers import MissionSerializer, MissionCreateSerializer, MissionViewSerializer

from .views_base import ChatbotView, parse_datetime, parse_none

_mission_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties=OrderedDict((
        ("id", openapi.Schema(type=openapi.TYPE_STRING)),
        ("name", openapi.Schema(type=openapi.TYPE_STRING)),
        ("description", openapi.Schema(type=openapi.TYPE_STRING)),
        ("username", openapi.Schema(type=openapi.TYPE_STRING)),
        ("organization", openapi.Schema(type=openapi.TYPE_STRING)),
        ("start", openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME)),
        ("end", openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME)),
        ("status", openapi.Schema(type=openapi.TYPE_STRING, example="Created")),
        ("source", openapi.Schema(type=openapi.TYPE_STRING, example="Chatbot")),
        ("reports", openapi.Schema(type=openapi.TYPE_OBJECT, example=[
            {"name": "Report N", "id": "N"}
        ])),
        ("geometry", openapi.Schema(type=openapi.TYPE_OBJECT, example={
            "type": "Point",
            "coordinates": [1,2]
        })),
        ("location", openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_NUMBER), example=[1, 2])),
    ))
)  # yapf: disable


_mission_list_schema = openapi.Schema(
    type=openapi.TYPE_ARRAY, items=_mission_schema
)

_mission_create_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties=OrderedDict((("msg", openapi.Schema(type=openapi.TYPE_STRING)), )
                          )
)


class MissionView(ChatbotView):

    view_serializer_class = MissionViewSerializer
    model_serializer_class = MissionSerializer


class MissionListView(MissionView):

    GATEWAY_URL_LIST_PATH = "/api/services/app/Missions/GetMissions"
    GATEWAY_URL_CREATE_PATH = "/api/services/app/Missions/CreateOrUpdateMission"

    @swagger_auto_schema(
        query_serializer=MissionViewSerializer,
        responses={status.HTTP_200_OK: _mission_list_schema},
    )
    def get(self, request, *args, **kwargs):
        """
        list view
        """
        proxy_data = self.get_proxy_list_data(
            request,
            proxy_url=urljoin(
                settings.SAFERS_GATEWAY_API_URL, self.GATEWAY_URL_LIST_PATH
            ),
        )

        missions = [
            Mission(
                mission_id=data["id"],
                title=data.get("title"),
                description=data.get("description"),
                # TODO: username=data.get(),
                organization=data.get("organization", {}).get("name"),
                start=parse_datetime(data["duration"]["lowerBound"]),
                start_inclusive=data["duration"].get(
                    "lowerBoundIsInclusive", False
                ),
                end=parse_datetime(data["duration"]["upperBound"]),
                end_inclusive=data["duration"].get(
                    "upperBoundIsInclusive", False
                ),
                # TODO: PROXY IS SENDING A NUMBER - I NEED TO MAP THAT TO ONE OF MissionStatusType.choices
                # status=data.get("currentStatus"),
                reports=[{
                    "id": report.get("id"),
                    "name": f"Report {report.get('id')}",
                } for report in data.get("reports", [])],
                geometry=geos.Point(
                    data["centroid"]["longitude"], data["centroid"]["latitude"]
                ) if data.get("centroid") else None,
            ) for data in proxy_data
        ]

        model_serializer = self.model_serializer_class(
            missions, context=self.get_serializer_context(), many=True
        )

        return Response(data=model_serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=MissionCreateSerializer,
        responses={status.HTTP_200_OK: _mission_create_schema}
    )
    def post(self, request, *args, **kwargs):
        """
        create view
        """

        serializer = MissionCreateSerializer(
            data=request.data,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        instance = Mission(**serializer.validated_data)

        proxy_data = serializer.to_representation(instance=instance)
        proxy_data = {
            "feature": {
                "geometry":
                    json.dumps(proxy_data.pop("geometry"), cls=JSONEncoder),
                "properties":
                    json.loads(
                        json.dumps(
                            proxy_data.pop("properties"), cls=JSONEncoder
                        )
                    )
            }
        }

        proxy_url = urljoin(
            settings.SAFERS_GATEWAY_API_URL, self.GATEWAY_URL_CREATE_PATH
        )

        try:
            response = requests.post(
                proxy_url,
                auth=ProxyAuthentication(request.user),
                headers={"Content-Type": "application/json"},
                json=proxy_data,
                timeout=4,
            )
            response.raise_for_status()

        except Exception as e:
            raise APIException(e)

        instance.mission_id = response.json()
        msg = f"successfully created {instance.name}."

        return Response({"msg": msg}, status=status.HTTP_200_OK)


_mission_statuses_schema = openapi.Schema(
    type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)
)


@swagger_auto_schema(
    responses={status.HTTP_200_OK: _mission_statuses_schema}, method="get"
)
@api_view(["GET"])
@permission_classes([AllowAny])
def mission_statuses_view(request):
    """
    Returns the list of possible Mission statuses.
    """
    return Response(MissionStatusTypes.values, status=status.HTTP_200_OK)
