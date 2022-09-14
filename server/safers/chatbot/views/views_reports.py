import requests
from urllib.parse import urljoin

from django.conf import settings
from django.contrib.gis import geos

from rest_framework import status, views
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import APIException
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from safers.users.authentication import ProxyAuthentication

from safers.chatbot.models import Report, ReportCategory
from safers.chatbot.serializers import ReportSerializer, ReportViewSerializer

from .views_base import ChatbotView, parse_none, parse_datetime

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
        "categories": [
            "Measurements"
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
)


class ReportView(ChatbotView):

    view_serializer_class = ReportViewSerializer
    model_serializer_class = ReportSerializer


class ReportListView(ReportView):

    GATEWAY_URL_LIST_PATH = "/api/services/app/Reports/GetReports"

    @swagger_auto_schema(
        query_serializer=ReportViewSerializer,
        responses={status.HTTP_200_OK: _report_list_schema},
    )
    def get(self, request, *args, **kwargs):

        proxy_data = self.get_proxy_list_data(
            request,
            proxy_url=urljoin(
                settings.SAFERS_GATEWAY_API_URL, self.GATEWAY_URL_LIST_PATH
            ),
        )

        report_categories = {
            # hitting the db once outside of the list comprehension below
            # instead of hitting it for every report in proxy_data
            report_category.pop("category_id"): report_category
            for report_category in ReportCategory.objects.values(
                "category_id",
                "name",
                "group",
                "sub_group",
                "unit_of_measure",
            )
        }

        reports = [
            Report(
                report_id=data.get("id"),
                mission_id=data.get("relativeMissionId"),
                timestamp=parse_datetime(data.get("timestamp")),
                source=parse_none(data.get("source")),
                hazard=parse_none(data.get("hazard")),
                status=parse_none(data.get("status")),
                content=parse_none(data.get("content")),
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
                categories=[
                    {
                        "group": report_categories[extension["categoryId"]]["group"],
                        "sub_group": report_categories[extension["categoryId"]]["sub_group"],
                        "name": report_categories[extension["categoryId"]]["name"],
                        "units": report_categories[extension["categoryId"]]["unit_of_measure"],
                        "value": extension.get("value"),
                        "status": extension.get("status"),
                    }
                    for extension in data.get("extensionData", [])
                    if extension.get("categoryId") in report_categories
                ]
            ) for data in proxy_data
        ]  # yapf: disable

        model_serializer = self.model_serializer_class(
            reports, context=self.get_serializer_context(), many=True
        )

        return Response(data=model_serializer.data, status=status.HTTP_200_OK)


class ReportDetailView(ReportView):

    GATEWAY_URL_DETAIL_PATH = "/api/services/app/Reports/GetReportById"

    @swagger_auto_schema(
        query_serializer=ReportViewSerializer,
        responses={status.HTTP_200_OK: _report_schema},
    )
    def get(self, request, *args, **kwargs):

        proxy_params = {
            "Id": kwargs["report_id"],
            "IncludeArea": True,
        }

        try:
            response = requests.get(
                urljoin(settings.SAFERS_GATEWAY_API_URL, self.GATEWAY_URL_DETAIL_PATH),
                auth=ProxyAuthentication(request.user),
                params=proxy_params,
                timeout=4,  # 4 seconds as per https://requests.readthedocs.io/en/stable/user/advanced/#timeouts
            )  # yapf: disable
            response.raise_for_status()
            proxy_data = response.json()
        except Exception as e:
            raise APIException(e)

        feature = proxy_data["feature"]
        geometry = feature.get("geometry", None)
        properties = feature.get("properties", {})

        report_categories = {
            report_category.pop("category_id"): report_category
            for report_category in ReportCategory.objects.values(
                "category_id",
                "name",
                "group",
                "sub_group",
                "unit_of_measure",
            )
        }
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
            categories=[
                {
                    "group": report_categories[extension["categoryId"]]["group"],
                    "sub_group": report_categories[extension["categoryId"]]["sub_group"],
                    "name": report_categories[extension["categoryId"]]["name"],
                    "units": report_categories[extension["categoryId"]]["unit_of_measure"],
                    "value": extension.get("value"),
                    "status": extension.get("status"),
                }
                for extension in properties.get("extensionData", [])
                if extension.get("categoryId") in report_categories
            ]
        )  # yapf: disable

        model_serializer = self.model_serializer_class(
            report, context=self.get_serializer_context(), many=False
        )

        return Response(data=model_serializer.data, status=status.HTTP_200_OK)


_report_categories_schema = openapi.Schema(
    type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)
)


@swagger_auto_schema(
    responses={status.HTTP_200_OK: _report_categories_schema}, method="get"
)
@api_view(["GET"])
@permission_classes([AllowAny])
def report_categories_view(request):
    """
    Returns the list of possible Report categories.
    """
    report_categories_groups = ReportCategory.objects.values_list(
        "group", flat=True
    ).distinct()
    return Response(report_categories_groups, status=status.HTTP_200_OK)


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
