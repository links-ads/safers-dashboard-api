import requests
from collections import OrderedDict
from datetime import datetime, timedelta
from itertools import repeat
from urllib.parse import quote_plus, urlencode, urljoin

from django.conf import settings

from rest_framework import status, views
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from safers.core.models import SafersSettings
from safers.core.utils import chunk

from safers.users.authentication import ProxyAuthentication
from safers.users.exceptions import AuthenticationException
from safers.users.permissions import IsRemote

from safers.data.models import DataType
from safers.data.serializers import DataLayerViewSerializer
from safers.data.utils import extent_to_scaled_resolution

###########
# swagger #
###########

_data_layer_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    example={
        "id": "1",
        "text": "Weather forecast",
        "domain": None,
        "source": None,
        "info": "whatever",
        "info_url": None,
        "children": [
          {
            "id": "1.1",
            "text": "Short term",
            "domain": None,
            "source": None,
            "info": "whatever",
            "info_url": None,
            "children": [
              {
                "id": "1.1.1",
                "text": "Temperature at 2m",
                "units": "°C",
                "domain": "Weather",
                "source": "RISC",
                "info": "whatever",
                "info_url": None,
                "children": [
                  {
                    "id": "1.1.1.1",
                    "text": "2022-04-28T12:15:20Z",
                    "title": "Temperature at 2m",
                    "units": "°C",
                    "info": None,
                    "info_url": "http://localhost:8000/api/data/layers/metadata/02bae14e-c24a-4264-92c0-2cfbf7aa65f5?metadata_format=text",
                    "metadata_url": "http://localhost:8000/api/data/layers/metadata/02bae14e-c24a-4264-92c0-2cfbf7aa65f5?metadata_format=json",
                    "legend_url": "https://geoserver-test.safers-project.cloud/geoserver/ermes/wms?layer=ermes%3A33101_t2m_33001_b7aa380a-20fc-41d2-bfbc-a6ca73310f4d&service=WMS&request=GetLegendGraphic&srs=EPSG%3A4326&width=256&height=256&format=image%2Fpng",
                    "pixel_url": "https://geoserver-test.safers-project.cloud/geoserver/ermes/wms?request=GetFeatureInfo...",
                    "timeseries_urls": [
                      "https://geoserver-test.safers-project.cloud/geoserver/ermes/wms?request=GeTimeSeries...",
                      "https://geoserver-test.safers-project.cloud/geoserver/ermes/wms?request=GeTimeSeries...",
                    ],
                    "timeseries_url": "https://geoserver-test.safers-project.cloud/geoserver/ermes/wms?request=GeTimeSeries...",
                    "urls": {
                      "2022-04-28T12:15:20Z": "https://geoserver-test.safers-project.cloud/geoserver/ermes/wms?time=2022-04-28T12%3A15%3A20Z&layers=ermes%3A33101_t2m_33001_b7aa380a-20fc-41d2-bfbc-a6ca73310f4d&service=WMS&request=GetMap&srs=EPSG%3A4326&bbox={bbox}&width=256&height=256&format=image%2Fpng",
                      "2022-04-28T13:15:20Z": "https://geoserver-test.safers-project.cloud/geoserver/ermes/wms?time=2022-04-28T13%3A15%3A20Z&layers=ermes%3A33101_t2m_33001_b7aa380a-20fc-41d2-bfbc-a6ca73310f4d&service=WMS&request=GetMap&srs=EPSG%3A4326&bbox={bbox}&width=256&height=256&format=image%2Fpng",
                      "2022-04-28T14:15:20Z": "https://geoserver-test.safers-project.cloud/geoserver/ermes/wms?time=2022-04-28T14%3A15%3A20Z&layers=ermes%3A33101_t2m_33001_b7aa380a-20fc-41d2-bfbc-a6ca73310f4d&service=WMS&request=GetMap&srs=EPSG%3A4326&bbox={bbox}&width=256&height=256&format=image%2Fpng",
                    }
                }
              ]
            }
          ]
        }
      ]
    }
)  # yapf: disable


_data_layer_list_schema = openapi.Schema(
    type=openapi.TYPE_ARRAY, items=_data_layer_schema
)  # yapf: disable


_data_layer_sources_schema = openapi.Schema(
    type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)
)  # yapf: disable


_data_layer_domains_schema = openapi.Schema(
    type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)
)  # yapf: disable


#########
# views #
#########


class DataLayerView(views.APIView):

    permission_classes = [IsAuthenticated, IsRemote]
    serializer_class = DataLayerViewSerializer

    def get_serializer_context(self):
        """
        Extra context provided to the serializer class.
        (If this were some type of ModelView, this fn would be built-in.)
        """

        return {
            'request': self.request, 'format': self.format_kwarg, 'view': self
        }

    ## REMOVED TIMESTAMP/BBOX FILTERING AS PER https://astrosat.atlassian.net/browse/SAFB-255
    ##
    ## def update_default_data(self, data):
    ##
    ##     if data.pop("default_bbox") and "bbox" not in data:
    ##         user = self.request.user
    ##         default_bbox = user.default_aoi.geometry.extent
    ##         data["bbox"] = ",".join(map(str, default_bbox))
    ##
    ##     default_date = data.pop("default_date")
    ##     if default_date and "start" not in data:
    ##         data["start"] = timezone.now() - timedelta(days=3)
    ##     if default_date and "end" not in data:
    ##         data["end"] = timezone.now()
    ##
    ##     # as per https://stackoverflow.com/a/42777551/1060339, DateTimeField doesn't
    ##     # automatically output "Z" for UTC timezone; so put it in explicitly
    ##     if "start" in data:
    ##         data["start"] = data["start"].strftime('%Y-%m-%dT%H:%M:%SZ')
    ##     if "end" in data:
    ##         data["end"] = data["end"].strftime('%Y-%m-%dT%H:%M:%SZ')
    ##
    ##     return data

    @swagger_auto_schema(
        query_serializer=DataLayerViewSerializer,
        responses={status.HTTP_200_OK: _data_layer_list_schema}
    )
    def get(self, request, *args, **kwargs):
        """
        Returns a hierarchy of available DataLayers. 
        Each leaf-node provides a URL paramter to retrieve the actual layer.
        """

        GATEWAY_URL_PATH = "/api/services/app/Layers/GetLayers"
        GEOSERVER_URL_PATH = "/geoserver/ermes/wms"
        METADATA_URL_PATH = "/api/data/layers/metadata"

        MAX_GEOSERVER_TIMES = 100  # the maximum timestamps that can be passed to GetTimeSeries at once

        safers_settings = SafersSettings.load()
        max_resolution = safers_settings.map_request_resolution
        # if safers_settings.restrict_data_to_aoi:
        #     width, height = extent_to_scaled_resolution(request.user.default_aoi.geometry.extent, max_resolution)
        # else:
        #     width, height = repeat(max_resolution, 2)
        width, height = repeat(max_resolution, 2)

        serializer = self.serializer_class(
            data=request.query_params,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)

        ## REMOVED TIMESTAMP/BBOX FILTERING AS PER https://astrosat.atlassian.net/browse/SAFB-255
        ## updated_data = self.update_default_data(serializer.validated_data)

        proxy_params = {
            serializer.ProxyFieldMapping[k]: v
            for k, v in serializer.validated_data.items()
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

        geoserver_layer_query_params = urlencode(
            {
                "time": "{time}",
                "layers": "{name}",
                "service": "WMS",
                "request": "GetMap",
                "srs": "EPSG:4326",
                "version": "1.1.0",
                "bbox": "{{bbox}}",
                "transparent": True,
                "width": width,  # max_resolution,
                "height": height,  # max_resolution,
                "format": "image/png",
            },
            safe="{}",
        )
        geoserver_layer_url = f"{urljoin(settings.SAFERS_GEOSERVER_API_URL, GEOSERVER_URL_PATH)}?{geoserver_layer_query_params}"

        geoserver_legend_query_params = urlencode(
            {
                "layer": "{name}",
                "service": "WMS",
                "request": "GetLegendGraphic",
                "srs": "EPSG:4326",
                "width": 512,
                "height": 256,
                "format": "image/png",
                "LEGEND_OPTIONS": "fontsize:80;dpi=72"
            },
            safe="{}",
        )
        geoserver_legend_url = f"{urljoin(settings.SAFERS_GEOSERVER_API_URL, GEOSERVER_URL_PATH)}?{geoserver_legend_query_params}"

        geoserver_pixel_query_params = urlencode(
            {
                "service": "WMS",
                "version": "1.1.0",
                "request": "GetFeatureInfo",
                "srs": "EPSG:4326",
                "info_format": "application/json",
                "layers": "{name}",
                "query_layers": "{name}",
                "width": 1,
                "height": 1,
                "x": 1,
                "y": 1,
                "bbox": "{{bbox}}",
            },
            safe="{}",
        )
        geoserver_pixel_url = f"{urljoin(settings.SAFERS_GEOSERVER_API_URL, GEOSERVER_URL_PATH)}?{geoserver_pixel_query_params}"

        geoserver_timeseries_query_params = urlencode(
            # this seems unintuitive, but the GetTimeseries Geoserver API uses the bbox (not x & y)
            # to determine the region to inspect - therefore I set height & width & x & y to constants
            # and the frontend injects a pixel-sized bbox into the query
            {
                "service": "WMS",
                "version": "1.1.0",
                "request": "GetTimeSeries",
                "srs": "EPSG:4326",
                "format":
                    "text/csv",  # "image/png" or "image/jpg" or "text/csv"
                "styles": "raw",
                "time": "{time}",
                "layers": "{name}",
                "query_layers": "{name}",
                "width": 1,
                "height": 1,
                "x": 1,
                "y": 1,
                "bbox": "{{bbox}}",
            },
            safe="{}",
        )
        geoserver_timeseries_url = f"{urljoin(settings.SAFERS_GEOSERVER_API_URL, GEOSERVER_URL_PATH)}?{geoserver_timeseries_query_params}"

        metadata_url = f"{self.request.build_absolute_uri(METADATA_URL_PATH)}/{{metadata_id}}?metadata_format={{metadata_format}}"

        data_type_info = {"None": None}
        data_type_sources = {"None": None}
        data_type_domains = {"None": None}
        for data_type in DataType.objects.operational():
            data_type_key = (
                data_type.datatype_id or data_type.subgroup or data_type.group
            ).upper()
            data_type_info[data_type_key] = data_type.info or data_type.description  # yapf: disable
            data_type_sources[data_type_key] = data_type.source
            data_type_domains[data_type_key] = data_type.domain

        content = response.json()

        data = [
          {
            "id": f"{i}",
            "text": group["group"],
            "domain": data_type_domains.get(group["group"].upper()),
            "source": data_type_sources.get(group["group"].upper()),
            "info": data_type_info.get(group["group"].upper()),
            "info_url": None,
            "children": [
              {
                "id": f"{i}.{j}",
                "text": sub_group["subGroup"],
                "domain": data_type_domains.get(sub_group["subGroup"].upper()),
                "source": data_type_sources.get(sub_group["subGroup"].upper()),
                "info": data_type_info.get(sub_group["subGroup"].upper()),
                "info_url": None,
                "children": [
                  {
                    "id": f"{i}.{j}.{k}",
                    "text": layer["name"],
                    "units": layer.get("unitOfMeasure"),
                    "domain": data_type_domains.get(str(layer.get("dataTypeId"))),
                    "source": data_type_sources.get(str(layer.get("dataTypeId"))),
                    "info": data_type_info.get(str(layer.get("dataTypeId"))),
                    "info_url": None,
                    "children": [
                      {
                        # "data_type": detail.get("dataTypeId"),
                        "id": f"{i}.{j}.{k}.{l}",
                        "title": layer["name"],
                        "text": next(iter(detail.get("timestamps") or []), None),
                        "units": layer.get("unitOfMeasure"),
                        "info": None,
                        "info_url": metadata_url.format(
                            metadata_id=detail.get("metadata_Id"),
                            metadata_format="text",
                        ),
                        "metadata_url": metadata_url.format(
                            metadata_id=detail.get("metadata_Id"),
                            metadata_format="json",
                        ),
                        "legend_url": geoserver_legend_url.format(
                            name=quote_plus(detail["name"]),
                        ),
                        "pixel_url": geoserver_pixel_url.format(
                            name=quote_plus(detail["name"]),
                        ),
                        "timeseries_urls": [
                          geoserver_timeseries_url.format(
                            name=quote_plus(detail["name"]),
                            time=quote_plus(",".join(timestamps_chunk)),
                          )
                          for timestamps_chunk in chunk(detail["timestamps"], MAX_GEOSERVER_TIMES)
                        ] if len(detail.get("timestamps", [])) > 1 else None,
                        "timeseries_url": geoserver_timeseries_url.format(
                            name=quote_plus(detail["name"]),
                            time=quote_plus(",".join(detail["timestamps"])),
                        ) if len(detail.get("timestamps", [])) > 1 else None,
                        "urls": OrderedDict(
                          [
                            (
                                timestamp,
                                geoserver_layer_url.format(
                                  name=quote_plus(detail["name"]),
                                  time=quote_plus(timestamp),
                                )
                            )
                            for timestamp in detail.get("timestamps", [])
                          ]
                        )
                      }
                      for l, detail in enumerate(
                        sorted(layer.get("details"), key=lambda x: x.get("created_At"), reverse=True) or [],
                        start=1
                      )
                      if l <= serializer.validated_data["n_layers"]
                    ]
                  }
                  for k, layer in enumerate(sub_group.get("layers") or [], start=1)
                ]
              }
              for j, sub_group in enumerate(group.get("subGroups") or [], start=1)
            ]
          } for i, group in enumerate(content.get("layerGroups") or [], start=1)
        ]  # yapf: disable

        return Response(data)


@swagger_auto_schema(
    responses={status.HTTP_200_OK: _data_layer_domains_schema}, method="get"
)
@api_view(["GET"])
@permission_classes([AllowAny])
def data_layer_domains_view(request):
    """
    Returns the list of possible DataLayer domains.
    """
    data_type_domains = DataType.objects.operational().only("domain").exclude(
        domain__isnull=True
    ).order_by("domain").values_list("domain", flat=True).distinct()
    return Response(data_type_domains, status=status.HTTP_200_OK)


@swagger_auto_schema(
    responses={status.HTTP_200_OK: _data_layer_sources_schema}, method="get"
)
@api_view(["GET"])
@permission_classes([AllowAny])
def data_layer_sources_view(request):
    """
    Returns the list of possible DataLayer sources.
    """
    data_type_sources = DataType.objects.operational().only("source").exclude(
        source__isnull=True
    ).order_by("source").values_list("source", flat=True).distinct()
    return Response(data_type_sources, status=status.HTTP_200_OK)


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
