import json
import logging
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

from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiTypes, OpenApiExample

from safers.core.authentication import TokenAuthentication

from safers.chatbot.models import Mission, MissionStatusChoices
from safers.chatbot.serializers import MissionSerializer, MissionCreateSerializer, MissionViewSerializer

from .views_base import ChatbotView, parse_datetime, parse_none

logger = logging.getLogger(__name__)


class MissionView(ChatbotView):

    view_serializer_class = MissionViewSerializer
    model_serializer_class = MissionSerializer


class MissionListView(MissionView):

    GATEWAY_URL_LIST_PATH = "/api/services/app/Missions/GetMissions"
    GATEWAY_URL_CREATE_PATH = "/api/services/app/Missions/CreateOrUpdateMission"

    @extend_schema(
        request=MissionViewSerializer,
        responses={status.HTTP_200_OK: MissionSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        """
        list view
        """
        proxy_data = self.get_proxy_list_data(
            request,
            proxy_url=urljoin(
                settings.SAFERS_GATEWAY_URL, self.GATEWAY_URL_LIST_PATH
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
                status=MissionStatusChoices.find_enum(
                    data.get("currentStatus")
                ),
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

    @extend_schema(
        request=MissionCreateSerializer,
        responses={
            status.HTTP_200_OK:
                OpenApiResponse(
                    OpenApiTypes.OBJECT,
                    examples=[
                        OpenApiExample(
                            "valid responese",
                            {"msg": "successfully created <name>"}
                        )
                    ]
                )
        }
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

        try:
            response = requests.post(
                urljoin(
                    settings.SAFERS_GATEWAY_URL,
                    self.GATEWAY_URL_CREATE_PATH,
                ),
                auth=TokenAuthentication(request.auth),
                headers={"Content-Type": "application/json"},
                json=proxy_data,
                timeout=4,
            )
            response.raise_for_status()

        except Exception as e:
            logger.error("##############################")
            logger.error("error creating mission")
            logger.error(response.json())
            logger.error("##############################")
            raise APIException(e)

        instance.mission_id = response.json()
        msg = f"successfully created {instance.name}."

        return Response({"msg": msg}, status=status.HTTP_200_OK)


@extend_schema(
    request=None,
    responses={
        status.HTTP_200_OK:
            OpenApiResponse(
                OpenApiTypes.ANY,
                examples=[
                    OpenApiExample(
                        "valid response", MissionStatusChoices.values
                    )
                ]
            ),
    }
)
@api_view(["GET"])
@permission_classes([AllowAny])
def mission_statuses_view(request):
    """
    Returns the list of possible Mission statuses.
    """
    return Response(MissionStatusChoices.values, status=status.HTTP_200_OK)
