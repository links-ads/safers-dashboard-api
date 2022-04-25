import requests
from copy import deepcopy
from datetime import datetime, timedelta
from urllib.parse import quote_plus, urlencode, urljoin

from django.conf import settings
from django.utils import timezone

from rest_framework import generics, mixins, views, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from safers.users.authentication import ProxyAuthentication, ProxyBearerAuthentication
from safers.users.exceptions import AuthenticationException
from safers.users.permissions import IsRemote

from safers.data.models import DataLayer
from safers.data.serializers import DataLayerSerializer


class DataLayerListView(views.APIView):

    permission_classes = [IsAuthenticated, IsRemote]
    serializer_class = DataLayerSerializer

    def get_serializer_context(self):
        """
        Extra context provided to the serializer class.
        (If this were some type of ModelView, this fn would be built-in.)
        """

        return {
            'request': self.request, 'format': self.format_kwarg, 'view': self
        }

    def update_default_data(self, data):

        if "bbox" not in data and data.get("default_bbox"):
            user = self.request.user
            default_bbox = user.default_aoi.geometry.extent
            data["bbox"] = ",".join(map(str, default_bbox))
            # data["bbox"] = user.default_aoi.geometry.extent

        if "start" not in data and data.get("default_start"):
            data["start"] = timezone.now() - timedelta(days=3)

        if "end" not in data and data.get("default_end"):
            data["end"] = timezone.now()

        return data

    @swagger_auto_schema(query_serializer=DataLayerSerializer)
    def get(self, request, *args, **kwargs):

        GATEWAY_URL_PATH = "/api/services/app/Layers/GetLayers"
        GEOSERVER_URL_PATH = "/geoserver/ermes/wms"

        # PROXY_URL = "/layers"

        serializer = self.serializer_class(
            data=request.query_params,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)

        updated_data = self.update_default_data(serializer.validated_data)
        proxy_params = {
            serializer.ProxyFieldMapping[k]: v
            for k, v in updated_data.items()
            if k in serializer.ProxyFieldMapping
        }  # yapf: disable

        try:
            response = requests.get(
                urljoin(settings.SAFERS_GATEWAY_API_URL, GATEWAY_URL_PATH),
                auth=ProxyAuthentication(request.user),
                params=proxy_params,
            )
            response.raise_for_status()
        except Exception as e:
            raise AuthenticationException(e)

        geoserver_query_params = urlencode(
            {
                "time": "{time}",
                "layers": "{name}",
                "service": "WMS",
                "request": "GetMap",
                "srs": "EPSG:4326",
                "bbox": "{bbox}",
                "width": 256,
                "height": 256,
                "fmt": "image/png",
            },
            safe="{}",
        )
        geoserver_url = f"{urljoin(settings.SAFERS_GEOSERVER_API_URL, GEOSERVER_URL_PATH)}?{geoserver_query_params}"

        data = response.json()
        data = [
          {
            "id": f"{i}",
            "text": group["group"],
            "children": [
              {
                "id": f"{i}.{j}",
                "text": sub_group["subGroup"],
                "children": [
                  {
                    "id": f"{i}.{j}.{k}",
                    "text": layer["name"],
                    "children": [
                      {
                        "id": f"{i}.{j}.{k}.{l}",
                        "text": detail["created_At"],
                        "type": "WMS",
                        "metadata_id": detail.get("metadata_Id"),
                        "url": geoserver_url.format(
                          name=quote_plus(detail["name"]),
                          time=quote_plus(detail["created_At"]),
                          bbox="{bbox}"
                        )
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