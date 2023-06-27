import json
import requests
from urllib.parse import urljoin

from django.conf import settings
from django.contrib.gis import geos

from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.utils.encoders import JSONEncoder

from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiTypes, OpenApiExample

from safers.core.authentication import TokenAuthentication

from safers.users.models import Organization

from safers.chatbot.models import Communication
from safers.chatbot.serializers import CommunicationSerializer, CommunicationCreateSerializer, CommunicationViewSerializer

from .views_base import ChatbotView, parse_datetime, parse_none


class CommunicationView(ChatbotView):

    view_serializer_class = CommunicationViewSerializer
    model_serializer_class = CommunicationSerializer


class CommunicationListView(CommunicationView):

    GATEWAY_URL_LIST_PATH = "/api/services/app/Communications/GetCommunications"
    GATEWAY_URL_CREATE_PATH = "/api/services/app/Communications/CreateOrUpdateCommunication"

    @extend_schema(
        request=CommunicationViewSerializer,
        responses={status.HTTP_200_OK: CommunicationSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        """
        Return all communications for the user making the request
        """
        proxy_data = self.get_proxy_list_data(
            request,
            proxy_url=urljoin(
                settings.SAFERS_GATEWAY_URL, self.GATEWAY_URL_LIST_PATH
            ),
        )

        communications = [
            Communication(
                communication_id=data["id"],
                # TODO: source_organization=...
                start=parse_datetime(data["duration"]["lowerBound"]),
                start_inclusive=data["duration"].get(
                    "lowerBoundIsInclusive", False
                ),
                end=parse_datetime(data["duration"]["upperBound"]),
                end_inclusive=data["duration"].get(
                    "upperBoundIsInclusive", False
                ),
                # source= (source has a default value so no need to parse from proxy_data)
                scope=data.get("scope"),
                restriction=data.get("restriction"),
                source_organization=Organization.objects.get(name=data.get("organizationName")),
                target_organizations=filter(
                    None,
                    [
                        Organization.objects.get(id=organization_id)
                        for organization_id in data.get("organizationIdList") or []
                    ]
                ),
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

    @extend_schema(
        request=CommunicationCreateSerializer,
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
        Create a new communication.
        """
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
            settings.SAFERS_GATEWAY_URL, self.GATEWAY_URL_CREATE_PATH
        )

        try:
            response = requests.post(
                proxy_url,
                auth=TokenAuthentication(request.auth),
                headers={"Content-Type": "application/json"},
                json=proxy_data,
                timeout=4,
            )
            response.raise_for_status()

        except Exception as exeption:
            raise APIException(exeption) from exeption

        instance.communication_id = response.json(
        )["feature"]["properties"].get("id")
        msg = f"successfully created {instance.name}."

        return Response({"msg": msg}, status=status.HTTP_200_OK)
