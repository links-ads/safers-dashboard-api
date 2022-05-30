import requests
from urllib.parse import urljoin

from django.conf import settings
from django.contrib.gis import geos
from django.utils import timezone

from rest_framework import status, views
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from safers.users.authentication import ProxyAuthentication
from safers.users.permissions import IsRemote

from safers.chatbot.models import Report
from safers.chatbot.serializers import ReportSerializer, ReportViewSerializer

_report_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    example={
        "name": "Report 123",
        "report_id": "123",
        "mission_id": "456",
        "timestamp": "2022-05-04T13:19:15.004Z",
        "source": "Chatbot",
        "hazard": "Fire",
        "status": "Notified",
        "content": "Submitted",
        "visibility": "Private",
        "description": "report fire on the hills",
        "reporter": {
            "name": "first.responder.test.2",
            "organization": "Test Organization"
        },
        "media": [
            {
                "url": "https://safersblobstoragetest.blob.core.windows.net/reports/000019/113b8271-30b1-4987-a5d0-6ebac839bae2.jpeg",
                "thumbnail": "https://safersblobstoragetest.blob.core.windows.net/thumbnails/000019/113b8271-30b1-4987-a5d0-6ebac839bae2.jpeg",
                "type": "Image",
            },
        ],
        "geometry": {
            "type": "Point",
            "coordinates": [1, 2]
        },
        "location": [1, 2],
  }
)  # yapf: disable


_report_list_schema = openapi.Schema(
    type=openapi.TYPE_ARRAY, items=_report_schema
)  # yapf: disable

class ReportView(views.APIView):

    permission_classes = [IsAuthenticated, IsRemote]

    def get_serializer_context(self):
        return {
            'request': self.request, 'format': self.format_kwarg, 'view': self
        }


class ReportListView(ReportView):
    def update_default_data(self, data):

        if data.pop("default_start") and "start" not in data:
            data["start"] = timezone.now() - settings.SAFERS_DEFAULT_TIMERANGE

        if data.pop("default_end") and "end" not in data:
            data["end"] = timezone.now()

        if data.pop("default_bbox") and "bbox" not in data:
            user = self.request.user
            data["bbox"] = user.default_aoi.geometry.extent

        return data

    @swagger_auto_schema(
        query_serializer=ReportViewSerializer,
        responses={status.HTTP_200_OK: _report_list_schema},
    )
    def get(self, request, *args, **kwargs):
        """
        Return all reports
        """

        GATEWAY_URL_PATH = "/api/services/app/Reports/GetReports"

        view_serializer = ReportViewSerializer(
            data=request.query_params,
            context=self.get_serializer_context(),
        )
        view_serializer.is_valid(raise_exception=True)

        updated_data = self.update_default_data(view_serializer.validated_data)
        proxy_params = {
            view_serializer.ProxyFieldMapping[k]: v
            for k, v in updated_data.items()
            if k in view_serializer.ProxyFieldMapping
        }  # yapf: disable
        if "bbox" in proxy_params:
            min_x, min_y, max_x, max_y = proxy_params.pop("bbox")
            proxy_params["NorthEastBoundary.Latitude"] = max_x
            proxy_params["NorthEastBoundary.Longitude"] = max_y
            proxy_params["SouthWestBoundary.Latitude"] = min_x
            proxy_params["SouthWestBoundary.Longitude"] = min_y

        try:
            response = requests.get(
                urljoin(settings.SAFERS_GATEWAY_API_URL, GATEWAY_URL_PATH),
                auth=ProxyAuthentication(request.user),
                params=proxy_params,
            )
            response.raise_for_status()
        except Exception as e:
            raise APIException(e)

        reports = [
            Report(
                report_id=data.get("id"),
                mission_id=data.get("relativeMissionId"),
                timestamp=data.get("timestamp"),
                source=data.get("source"),
                hazard=data.get("hazard"),
                status=data.get("status"),
                content=data.get("content"),
                is_public=data.get("isPublic"),
                description=data.get("description"),
                geometry=geos.Point(
                    data["location"]["longitude"], data["location"]["latitude"]
                ) if data.get("location") else None,
                media=[{
                    "url": media_uri.get("mediaURI"),
                    "type": media_uri.get("mediaType"),
                    "thumbnail": media_uri.get("thumbnailURI"),
                } for media_uri in data.get("mediaURIs", [])],
                reporter={
                    "name": data.get("username"),
                    "organization": data.get("organizationName"),
                },
            ) for data in response.json()["data"]
        ]
        model_serializer = ReportSerializer(
            reports, context=self.get_serializer_context(), many=True
        )

        return Response(data=model_serializer.data, status=status.HTTP_200_OK)


class ReportDetailView(ReportView):
    @swagger_auto_schema(
        query_serializer=ReportViewSerializer,
        responses={status.HTTP_200_OK: _report_schema},
    )
    def get(self, request, *args, **kwargs):
        """
        Return all reports
        """

        GATEWAY_URL_PATH = "/api/services/app/Reports/GetReportById"

        proxy_params = {
            "Id": kwargs["report_id"],
            "IncludeArea": True,
        }

        try:

            response = requests.get(
                urljoin(settings.SAFERS_GATEWAY_API_URL, GATEWAY_URL_PATH),
                auth=ProxyAuthentication(request.user),
                params=proxy_params,
            )
            response.raise_for_status()
        except Exception as e:
            raise APIException(e)

        feature = response.json()["feature"]
        geometry = feature.get("geometry", None)
        properties = feature.get("properties", {})

        report = Report(
            report_id=properties.get("id"),
            mission_id=properties.get("relativeMissionId"),
            timestamp=properties.get("timestamp"),
            source=properties.get("source"),
            hazard=properties.get("hazard"),
            status=properties.get("status"),
            content=properties.get("content"),
            is_public=properties.get("isPublic"),
            description=properties.get("description"),
            geometry=geos.GEOSGeometry(geometry) if geometry else None,
            media=[{
                "url": media_uri.get("mediaURI"),
                "type": media_uri.get("mediaType"),
                "thumbnail": media_uri.get("thumbnailURI"),
            } for media_uri in properties.get("mediaURIs", [])],
            reporter={
                "name": properties.get("username"),
                "organization": properties.get("organizationName"),
            },
        )
        model_serializer = ReportSerializer(
            report, context=self.get_serializer_context(), many=False
        )

        return Response(data=model_serializer.data, status=status.HTTP_200_OK)


"""
SAMPLE PROXY DATA SHAPE (list):
[
  {
    'id': 19,
    'hazard': 'Fire',
    'status': 'Notified',
    'content': 'Submitted',
    'location': {
      'latitude': 45.065549,
      'longitude': 7.65952
    },
    'timestamp': '2022-05-04T13:19:15.004Z',
    'mediaURIs': [
      {
        'mediaURI': 'https://safersblobstoragetest.blob.core.windows.net/reports/000019/113b8271-30b1-4987-a5d0-6ebac839bae2.jpeg',
        'mediaType': 'Image'
      }
    ],
    'extensionData': [
      {
        'categoryId': 6,
        'value': '5',
        'status': 'Unknown'
      }
    ],
    'description': 'report fire on the hills',
    'username': 'first.responder.test.2',
    'organizationName': 'Test Organization',
    'source': 'Chatbot',
    'isEditable': False,
    'relativeMissionId': 2,
    'tags': [
      {
        'mediaURI': '113b8271-30b1-4987-a5d0-6ebac839bae2.jpeg',
        'confidence': 0.9999961853027344,
        'name': 'tree'
      }
    ],
    'adultInfo': [
      {
        'mediaURI': '113b8271-30b1-4987-a5d0-6ebac839bae2.jpeg',
        'isAdultContent': False,
        'isRacyContent': False,
        'isGoryContent': False,
        'adultScore': 0.001597181661054492,
        'racyScore': 0.0030028189066797495,
        'goreScore': 0.0031083079520612955
      }
    ],
    'isPublic': False
  }
]
"""
"""
SAMPLE PROXY DATA SHAPE (detail):
TODO
"""