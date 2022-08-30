import json
import requests
from collections import OrderedDict
from datetime import datetime
from urllib.parse import urljoin

from django.conf import settings
from django.contrib.gis import geos

from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.utils.encoders import JSONEncoder

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from safers.chatbot.models import Communication
from safers.chatbot.serializers import CommunicationSerializer, CommunicationCreateSerializer, CommunicationViewSerializer
from safers.users.authentication import ProxyAuthentication
from .views_base import ChatbotView

_communication_create_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties=OrderedDict((("msg", openapi.Schema(type=openapi.TYPE_STRING)), )
                          )
)


class CommunicationView(ChatbotView):

    view_serializer_class = CommunicationViewSerializer
    model_serializer_class = CommunicationSerializer


class CommunicationListView(CommunicationView):

    GATEWAY_URL_LIST_PATH = "/api/services/app/Communications/GetCommunications"
    GATEWAY_URL_CREATE_PATH = "/api/services/app/Communications/CreateOrUpdateCommunication"

    @swagger_auto_schema(
        query_serializer=CommunicationViewSerializer,
        responses={status.HTTP_200_OK: CommunicationSerializer},
    )
    def get(self, request, *args, **kwargs):

        proxy_data = self.get_proxy_list_data(
            request,
            proxy_url=urljoin(
                settings.SAFERS_GATEWAY_API_URL, self.GATEWAY_URL_LIST_PATH
            ),
        )

        communications = [
            Communication(
                communication_id=data["id"],
                # TODO: source_organization=...
                start=datetime.fromisoformat(
                    data["duration"]["lowerBound"].replace("Z", "+00:00")
                ),
                start_inclusive=data["duration"].get(
                    "lowerBoundIsInclusive", False
                ),
                end=datetime.fromisoformat(
                    data["duration"]["upperBound"].replace("Z", "+00:00")
                ),
                end_inclusive=data["duration"].get(
                    "upperBoundIsInclusive", False
                ),
                # source= (source has a default value so no need to parse from proxy_data)
                scope=data.get("scope"),
                restriction=data.get("restriction"),
                # TODO: SHOULD REALLY REPLACE assigned_to W/ target_organizations BUT HAVE TO WAIT
                # TODO: UNTIL I'VE LINKED FUSIONAUTH ORGANIZATIONS W/ DJANGO ORGANIZATIONS
                # target_organizations=
                assigned_to=[data.get("organizationName")] if data.get("organizationName") else [],
                message=data.get("message"),
                geometry=geos.Point(
                    data["centroid"]["longitude"], data["centroid"]["latitude"]
                ) if data.get("centroid") else None,
            ) for data in proxy_data
        ]  # yapf: disable

        model_serializer = self.model_serializer_class(
            communications, context=self.get_serializer_context(), many=True
        )

        return Response(data=model_serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=CommunicationCreateSerializer,
        responses={status.HTTP_200_OK: _communication_create_schema}
    )
    def post(self, request, *args, **kwargs):

        serializer = CommunicationCreateSerializer(
            data=request.data,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        instance = Communication(**serializer.validated_data)

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

        instance.communication_id = response.json(
        )["feature"]["properties"].get("id")
        msg = f"successfully created {instance.name}."

        return Response({"msg": msg}, status=status.HTTP_200_OK)
