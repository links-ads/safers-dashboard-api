from datetime import datetime
from urllib.parse import urljoin

from django.conf import settings
from django.contrib.gis import geos

from rest_framework import status
from rest_framework.response import Response

from drf_yasg.utils import swagger_auto_schema

from safers.chatbot.models import Communication
from safers.chatbot.serializers import CommunicationSerializer, CommunicationViewSerializer
from .views_base import ChatbotView


class CommunicationView(ChatbotView):

    view_serializer_class = CommunicationViewSerializer
    model_serializer_class = CommunicationSerializer


class CommunicationListView(CommunicationView):

    GATEWAY_URL_PATH = "/api/services/app/Communications/GetCommunications"

    @swagger_auto_schema(
        query_serializer=CommunicationViewSerializer,
        responses={status.HTTP_200_OK: CommunicationSerializer},
    )
    def get(self, request, *args, **kwargs):

        proxy_data = self.get_proxy_list_data(
            request,
            proxy_url=urljoin(
                settings.SAFERS_GATEWAY_API_URL, self.GATEWAY_URL_PATH
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
                # TODO: target_organizations=...
                message=data.get("message"),
                geometry=geos.Point(
                    data["centroid"]["longitude"], data["centroid"]["latitude"]
                ) if data.get("centroid") else None,
            ) for data in proxy_data
        ]

        model_serializer = self.model_serializer_class(
            communications, context=self.get_serializer_context(), many=True
        )

        return Response(data=model_serializer.data, status=status.HTTP_200_OK)
