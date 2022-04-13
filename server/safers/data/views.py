import requests
from collections import OrderedDict
from copy import deepcopy
from datetime import datetime, timedelta
from urllib.parse import urljoin

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.decorators import method_decorator

from rest_framework import status
from rest_framework import generics
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from django_filters import rest_framework as filters
from django_filters.utils import translate_validation

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from safers.core.filters import DefaultFilterSetMixin, CharInFilter

from safers.users.authentication import ProxyAuthentication
from safers.users.exceptions import AuthenticationException
from safers.users.permissions import IsRemote

from safers.data.models import DataLayer
from safers.data.serializers import DataLayerSerializer

###########
# swagger #
###########

_data_layer_manual_params = [
    # Bbox = CharInFilter(initial=DefaultFilterSetMixin.default_aoi_bbox)
    openapi.Parameter(
        "Start",
        openapi.IN_QUERY,
        type=openapi.TYPE_STRING,
        format=openapi.FORMAT_DATE,
    ),
    openapi.Parameter(
        "End",
        openapi.IN_QUERY,
        type=openapi.TYPE_STRING,
        format=openapi.FORMAT_DATE,
    ),
    openapi.Parameter(
        "MapRequestCode",
        openapi.IN_QUERY,
        type=openapi.TYPE_STRING,
    ),
    openapi.Parameter(
        "IncludeMapRequests",
        openapi.IN_QUERY,
        type=openapi.TYPE_BOOLEAN,
    ),
    openapi.Parameter(
        "ignore_proxy_filters",
        openapi.IN_QUERY,
        type=openapi.TYPE_BOOLEAN,
    ),
    openapi.Parameter(
        "order",
        openapi.IN_QUERY,
        type=openapi.TYPE_STRING,
        enum=["date", "-date"]
    )
]

###########
# filters #
###########

#########
# views #
#########


@method_decorator(
    swagger_auto_schema(query_serializer=DataLayerSerializer),
    name="list",
)
class DataLayerViewSet(viewsets.ViewSet):
    """
    Returns the DataLayers
    """

    lookup_url_kwarg = "data_layer_name"
    permission_classes = [IsAuthenticated, IsRemote]
    queryset = DataLayer.objects.none()

    def get_serializer_context(self):
        """
        Extra context provided to the serializer class.
        (If this were a ModelSerializer, this fn would be called by default.)
        """

        return {
            'request': self.request, 'format': self.format_kwarg, 'view': self
        }

    def update_default_data(self, data):

        if "bbox" not in data and data["default_bbox"]:
            user = self.request.user
            data["bbox"] = user.default_aoi.geometry.extent

        if "start" not in data and data["default_start"]:
            data["start"] = timezone.now() - timedelta(days=3)

        if "end" not in data and data["default_end"]:
            data["end"] = timezone.now()

        return data

    def list(self, request):

        PROXY_URL = "/api/services/app/Layers/GetLayers"
        # PROXY_URL = "/layers"

        serializer = DataLayerSerializer(
            data=request.query_params,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)

        updated_data = self.update_default_data(serializer.validated_data)

        proxy_params = {
            DataLayerSerializer.ProxyFieldMapping[k]: v
            for k, v in updated_data.items()
            if k in DataLayerSerializer.ProxyFieldMapping
        }  # yapf: disable

        try:
            response = requests.get(
                urljoin(settings.SAFERS_GATEWAY_API_URL, PROXY_URL),
                # urljoin(settings.SAFERS_GEODATA_API_URL, PROXY_URL),
                auth=ProxyAuthentication(request.user),
                params=proxy_params
            )
            response.raise_for_status()
        except Exception as e:
            raise AuthenticationException(e)

        data = response.json()

        data = [
          {
            "id": i,
            "text": group["group"],
            "children": [
              {
                "id": j,
                "text": sub_group["subGroup"],
                "children": [
                  {
                    "id": k,
                    "text": layer["name"],
                    "children": [
                      {
                        "id": l,
                        "date": detail["created_At"],
                        "name": detail["name"],
                      }
                      for l, detail in enumerate(layer.get("details") or [], start=1)
                    ]
                  }
                  for k, layer in enumerate(sub_group.get("layers") or [], start=1)
                ]
              }
              for j, sub_group in enumerate(group.get("subGroups") or [], start=1)
            ]
          } for i, group in enumerate(data.get("layerGroups") or [], start=1)
        ]  # yapf: disable

        return Response(data)

    def retrieve(self, request, data_layer_name=None):

        TEST_DATA_LAYER_NAME = "ermes:33101_t2m_33001_78a8a797-fb5c-4b40-9f12-88a64fffc616"
        PROXY_URL = "/api/action/resource_show"
        try:
            response = requests.get(
                # urljoin(settings.SAFERS_GATEWAY_API_URL, PROXY_URL),
                urljoin(settings.SAFERS_GEOSERVER_API_URL, PROXY_URL),
                auth=ProxyAuthentication(request.user),
            )
            response.raise_for_status()
        except Exception as e:
            raise AuthenticationException(e)

        data = {"hello": "world"}

        return Response(data)


"""
SAMPLE PROXY DATA SHAPE:
{
  "layerGroups": [
    {
      "groupKey": "weather forecast",
      "group": "Weather forecast",
      "subGroups": [
        {
          "subGroupKey": "short term",
          "subGroup": "Short term",
          "layers": [
            {
              "dataTypeId": 33101,
              "group": "Weather forecast",
              "groupKey": "weather forecast",
              "subGroup": "Short term",
              "subGroupKey": "short term",
              "name": "Temperature at 2m",
              "partnerName": "FMI",
              "type": "Forecast",
              "frequency": "H6",
              "details": [
                {
                  "name": "ermes:33101_t2m_33001_78a8a797-fb5c-4b40-9f12-88a64fffc616",
                  "timestamps": [
                    "2022-04-05T01:00:00Z",
                    "2022-04-05T02:00:00Z",
                  ],
                  "created_At": "2022-04-05T07:10:30Z",
                  "request_Code": null,
                  "mapRequestCode": null,
                  "creator": null
                }  
              ]
            },
            {
              "dataTypeId": 35007,
              "group": "Environment",
              "groupKey": "environment",
              "subGroup": "Forecast",
              "subGroupKey": "forecast",
              "name": "Fire perimeter simulation as isochrones maps",
              "partnerName": "CIMA",
              "type": "Forecast",
              "frequency": "OnDemand",
              "details": [
                {
                  "name": "ermes:35007_85f6e495-c258-437d-a447-190742071807",
                  "timestamps": [
                    "2021-12-12T16:00:00"
                  ],
                  "created_At": "2022-03-10T12:14:43Z",
                  "request_Code": null,
                  "mapRequestCode": null,
                  "creator": null
                }
              ]
            },
            {
              "dataTypeId": 35008,
              "group": "Environment",
              "groupKey": "environment",
              "subGroup": "Forecast",
              "subGroupKey": "forecast",
              "name": "Mean fireline intensity",
              "partnerName": "CIMA",
              "type": "Forecast",
              "frequency": "OnDemand",
              "details": [
                {
                  "name": "ermes:35008_efc92e30-3333-408e-83bb-fcc43f6b3280",
                  "timestamps": [
                    "2021-12-12T16:00:00"
                  ],
                  "created_At": "2022-03-10T12:14:47Z",
                  "request_Code": null,
                  "mapRequestCode": null,
                  "creator": null
                }
              ]
            },
            {
              "dataTypeId": 35009,
              "group": "Environment",
              "groupKey": "environment",
              "subGroup": "Forecast",
              "subGroupKey": "forecast",
              "name": "Max fireline intensity",
              "partnerName": "CIMA",
              "type": "Forecast",
              "frequency": "OnDemand",
              "details": [
                {
                  "name": "ermes:35009_67576ad9-95c8-4736-9f28-cf4c13bc11bd",
                  "timestamps": [
                    "2021-12-12T16:00:00"
                  ],
                  "created_At": "2022-03-10T12:14:49Z",
                  "request_Code": null,
                  "mapRequestCode": null,
                  "creator": null
                }
              ]
            },
            {
              "dataTypeId": 35010,
              "group": "Environment",
              "groupKey": "environment",
              "subGroup": "Forecast",
              "subGroupKey": "forecast",
              "name": "Mean rate of spread",
              "partnerName": "CIMA",
              "type": "Forecast",
              "frequency": "OnDemand",
              "details": [
                {
                  "name": "ermes:35010_ae63de06-9161-4f9e-bcb1-1e1ebb215688",
                  "timestamps": [
                    "2021-12-12T16:00:00"
                  ],
                  "created_At": "2022-03-10T12:14:44Z",
                  "request_Code": null,
                  "mapRequestCode": null,
                  "creator": null
                }
              ]
            },
            {
              "dataTypeId": 35011,
              "group": "Environment",
              "groupKey": "environment",
              "subGroup": "Forecast",
              "subGroupKey": "forecast",
              "name": "Max rate of spread",
              "partnerName": "CIMA",
              "type": "Forecast",
              "frequency": "OnDemand",
              "details": [
                {
                  "name": "ermes:35011_42dcea6e-d4cd-4ba0-be9f-e79d576c6f82",
                  "timestamps": [
                    "2021-12-12T16:00:00"
                  ],
                  "created_At": "2022-03-10T12:14:46Z",
                  "request_Code": null,
                  "mapRequestCode": null,
                  "creator": null
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
"""