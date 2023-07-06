from collections import OrderedDict
from datetime import datetime
from urllib.parse import quote_plus, urlencode, urljoin

from django.conf import settings

from rest_framework import status, views
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse, OpenApiTypes

from safers.core.authentication import TokenAuthentication
from safers.core.clients import GATEWAY_CLIENT
from safers.core.utils import chunk

from safers.data.models import DataType
from safers.data.serializers import LayerViewSerializer

###########
# swagger #
###########

_operational_layer_view_response = OpenApiResponse(
    OpenApiTypes.ANY,
    examples=[
        OpenApiExample(
            "valid response",
            [
                {
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
                                            "datatype_id": "31101",
                                            "id": "1.1.1.1",
                                            "text": "2022-04-28T12:15:20Z",
                                            "title": "Temperature at 2m",
                                            "units": "°C",
                                            "feature_string": "value of pixel: {{t2m}} °C",
                                            "info": None,
                                            "info_url": "http://localhost:8000/api/data/layers/metadata/02bae14e-c24a-4264-92c0-2cfbf7aa65f5?metadata_format=text",
                                            "metadata_url": "http://localhost:8000/api/data/layers/metadata/02bae14e-c24a-4264-92c0-2cfbf7aa65f5?metadata_format=json",
                                            "legend_url": "https://geoserver-test.safers-project.cloud/geoserver/ermes/wms?layer=ermes%3A33101_t2m_33001_b7aa380a-20fc-41d2-bfbc-a6ca73310f4d&service=WMS&request=GetLegendGraphic&srs=EPSG%3A4326&width=256&height=256&format=image%2Fpng",
                                            "pixel_url": "https://geoserver-test.safers-project.cloud/geoserver/ermes/wms?request=GetFeatureInfo...",
                                            "timeseries_urls": [
                                                "https://geoserver-test.safers-project.cloud/geoserver/ermes/wms?request=GeTimeSeries...",
                                                "https://geoserver-test.safers-project.cloud/geoserver/ermes/wms?request=GeTimeSeries...",
                                            ],
                                            "urls": {
                                                "2022-04-28T12:15:20Z": [
                                                    "https://geoserver-test1.safers-project.cloud/geoserver/gwc/service/wmts?time=2022-04-28T12%3A15%3A20Z&layer=ermes%3A33101_t2m_33001_b7aa380a-20fc-41d2-bfbc-a6ca73310f4d&service=WMTS&request=GetTile&srs=EPSG%3A900913&tilematrixset=EPSG%3A900913&tilematrix=EPSG%3A900913%3A{{z}}&tilecol={{x}}&tilerole={{y}}&format=image%2Fpng"
                                                    "https://geoserver-test2.safers-project.cloud/geoserver/gwc/service/wmts?time=2022-04-28T12%3A15%3A20Z&layer=ermes%3A33101_t2m_33001_b7aa380a-20fc-41d2-bfbc-a6ca73310f4d&service=WMTS&request=GetTile&srs=EPSG%3A900913&tilematrixset=EPSG%3A900913&tilematrix=EPSG%3A900913%3A{{z}}&tilecol={{x}}&tilerole={{y}}&format=image%2Fpng"
                                                ],
                                                "2022-04-28T13:15:20Z": [
                                                    "https://geoserver-test1.safers-project.cloud/geoserver/gwc/service/wmts?time=2022-04-28T13%3A15%3A20Z&layer=ermes%3A33101_t2m_33001_b7aa380a-20fc-41d2-bfbc-a6ca73310f4d&service=WMTS&request=GetTile&srs=EPSG%3A900913&tilematrixset=EPSG%3A900913&tilematrix=EPSG%3A900913%3A{{z}}&tilecol={{x}}&tilerole={{y}}&format=image%2Fpng",
                                                    "https://geoserver-test2.safers-project.cloud/geoserver/gwc/service/wmts?time=2022-04-28T13%3A15%3A20Z&layer=ermes%3A33101_t2m_33001_b7aa380a-20fc-41d2-bfbc-a6ca73310f4d&service=WMTS&request=GetTile&srs=EPSG%3A900913&tilematrixset=EPSG%3A900913&tilematrix=EPSG%3A900913%3A{{z}}&tilecol={{x}}&tilerole={{y}}&format=image%2Fpng"
                                                ],
                                                "2022-04-28T14:15:20Z": [
                                                    "https://geoserver-test1.safers-project.cloud/geoserver/gwc/service/wmts?time=2022-04-28T14%3A15%3A20Z&layer=ermes%3A33101_t2m_33001_b7aa380a-20fc-41d2-bfbc-a6ca73310f4d&service=WMTS&request=GetTile&srs=EPSG%3A900913&tilematrixset=EPSG%3A900913&tilematrix=EPSG%3A900913%3A{{z}}&tilecol={{x}}&tilerole={{y}}&format=image%2Fpng",
                                                    "https://geoserver-test2.safers-project.cloud/geoserver/gwc/service/wmts?time=2022-04-28T14%3A15%3A20Z&layer=ermes%3A33101_t2m_33001_b7aa380a-20fc-41d2-bfbc-a6ca73310f4d&service=WMTS&request=GetTile&srs=EPSG%3A900913&tilematrixset=EPSG%3A900913&tilematrix=EPSG%3A900913%3A{{z}}&tilecol={{x}}&tilerole={{y}}&format=image%2Fpng"
                                                ],
                                            }
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        )
    ]
)  # yapf: disable

_layer_domains_schema = OpenApiResponse(
    OpenApiTypes.ANY, examples=[OpenApiExample("valid response", [
        "string",
    ])]
)

#########
# views #
#########


class OperationalLayerView(views.APIView):

    permission_classes = [IsAuthenticated]
    serializer_class = LayerViewSerializer

    @extend_schema(
        request=None,
        responses={
            status.HTTP_200_OK: _operational_layer_view_response,
        }
    )
    def get(self, request, *args, **kwargs):
        """
        Returns a hierarchy of available DataLayers. 
        Each leaf-node provides a URL paramter to retrieve the actual layer.
        """

        DATETIME_INPUT_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
        DATETIME_OUTPUT_FORMAT = "%Y-%m-%dT%H:%M:%S.000Z"

        GEOSERVER_WMS_URL_PATH = "/geoserver/ermes/wms"
        GEOSERVER_WMTS_URL_PATH = "/geoserver/gwc/service/wmts"
        METADATA_URL_PATH = "/api/data/layers/metadata"

        WMS_CRS = "EPSG:4326"
        WMTS_CRS = "EPSG:900913"

        MAX_GEOSERVER_TIMES = 100  # the maximum timestamps that can be passed to GetTimeSeries at once

        serializer = self.serializer_class(
            data=request.query_params,
            context={"include_map_requests": False},
        )
        serializer.is_valid(raise_exception=True)

        operational_layers_data = GATEWAY_CLIENT.get_layers(
            auth=TokenAuthentication(request.auth),
            params=serializer.validated_data
        )

        geoserver_layer_query_params = urlencode(
            {
                "time": "{time}",
                "layer": "{name}",
                "service": "WMTS",
                "request": "GetTile",
                "version": "1.0.0",
                "transparent": True,
                "tilematrixset": WMTS_CRS,
                "tilematrix": WMTS_CRS + ":{{z}}",
                "tilecol": "{{x}}",
                "tilerow": "{{y}}",
                "format": "image/png",
            },
            safe="{}",
        )
        geoserver_layer_urls = [
            f"{urljoin(geoserver_api_url, GEOSERVER_WMTS_URL_PATH)}?{geoserver_layer_query_params}"
            for geoserver_api_url in settings.SAFERS_GEOSERVER_URLS
        ]

        geoserver_legend_query_params = urlencode(
            {
                "layer": "{name}",
                "service": "WMS",
                "request": "GetLegendGraphic",
                "srs": WMS_CRS,
                "width": 512,
                "height": 256,
                "format": "image/png",
                "LEGEND_OPTIONS": "fontsize:80;dpi=72"
            },
            safe="{}",
        )
        geoserver_legend_url = f"{urljoin(settings.SAFERS_GEOSERVER_URL, GEOSERVER_WMS_URL_PATH)}?{geoserver_legend_query_params}"

        geoserver_pixel_query_params = urlencode(
            {
                "service": "WMS",
                "version": "1.1.0",
                "request": "GetFeatureInfo",
                "srs": WMS_CRS,
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
        geoserver_pixel_url = f"{urljoin(settings.SAFERS_GEOSERVER_URL, GEOSERVER_WMS_URL_PATH)}?{geoserver_pixel_query_params}"

        geoserver_timeseries_query_params = urlencode(
            # this seems unintuitive, but the GetTimeseries Geoserver API uses the bbox (not x & y)
            # to determine the region to inspect - therefore I set height & width & x & y to constants
            # and the frontend injects a pixel-sized bbox into the query
            {
                "service": "WMS",
                "version": "1.1.0",
                "request": "GetTimeSeries",
                "srs": WMS_CRS,
                "format": "text/csv",
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
        geoserver_timeseries_url = f"{urljoin(settings.SAFERS_GEOSERVER_URL, GEOSERVER_WMS_URL_PATH)}?{geoserver_timeseries_query_params}"

        metadata_url = f"{self.request.build_absolute_uri(METADATA_URL_PATH)}/{{metadata_id}}?metadata_format={{metadata_format}}"

        data_type_info = {"None": None}
        data_type_sources = {"None": None}
        data_type_domains = {"None": None}
        data_type_feature_strings = {"None": None}
        data_type_opacity = {"None": None}
        for data_type in DataType.objects.operational():
            data_type_key = (
                data_type.datatype_id or data_type.subgroup or data_type.group
            ).upper()
            data_type_info[data_type_key] = data_type.info or data_type.description  # yapf: disable
            data_type_sources[data_type_key] = data_type.source
            data_type_domains[data_type_key] = data_type.domain
            data_type_feature_strings[data_type_key] = data_type.feature_string
            data_type_opacity[data_type_key] = data_type.opacity

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
                        "datatype_id": str(layer.get("dataTypeId")),
                        "id": f"{i}.{j}.{k}.{l}",
                        "title": layer["name"],
                        "text": next(iter(detail.get("timestamps") or []), None),
                        "units": layer.get("unitOfMeasure"),
                        "opacity": data_type_opacity.get(str(layer.get("dataTypeId"))),
                        "feature_string": data_type_feature_strings.get(str(layer.get("dataTypeId"))),
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
                        "urls": OrderedDict(
                          [
                            (
                                timestamp,
                                [
                                  url.format(
                                    name=quote_plus(detail["name"]),
                                    time=quote_plus(timestamp),
                                  )
                                  for url in geoserver_layer_urls
                                ]
                            )
                            for timestamp in map(
                              lambda x: datetime.strptime(x, DATETIME_INPUT_FORMAT).strftime(DATETIME_OUTPUT_FORMAT),
                              detail.get("timestamps", [])
                            )
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
          } for i, group in enumerate(operational_layers_data.get("layerGroups") or [], start=1)
        ]  # yapf: disable

        return Response(data)


@extend_schema(
    request=None, responses={
        status.HTTP_200_OK: _layer_domains_schema,
    }
)
@api_view(["GET"])
@permission_classes([AllowAny])
def operational_layer_domains_view(request):
    """
    Returns the list of possible OperationalLayer domains.
    """
    data_type_domains = DataType.objects.operational().only("domain").exclude(
        domain__isnull=True
    ).order_by("domain").values_list("domain", flat=True).distinct()
    return Response(data_type_domains, status=status.HTTP_200_OK)


@extend_schema(
    request=None, responses={
        status.HTTP_200_OK: _layer_domains_schema,
    }
)
@api_view(["GET"])
@permission_classes([AllowAny])
def on_demand_layer_domains_view(request):
    """
    Returns the list of possible OnDemandLayer domains.
    """
    data_type_domains = DataType.objects.on_demand().only("domain").exclude(
        domain__isnull=True
    ).order_by("domain").values_list("domain", flat=True).distinct()
    return Response(data_type_domains, status=status.HTTP_200_OK)
