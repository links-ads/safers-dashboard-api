from collections import OrderedDict, defaultdict
from datetime import datetime
from urllib.parse import quote_plus, urlencode, urljoin

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator

from rest_framework import mixins, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse, OpenApiTypes

from silk.profiling.profiler import silk_profile

from safers.core.decorators import swagger_fake
from safers.core.clients import GATEWAY_CLIENT

from safers.core.utils import chunk

from safers.data.models import MapRequest, DataType
from safers.data.permissions import IsReadOnlyOrOwner
from safers.data.serializers import LayerViewSerializer, MapRequestSerializer

from safers.rmq import RMQ_USER

from safers.core.authentication import TokenAuthentication

UserModel = get_user_model()

###########
# swagger #
###########

_map_request_schema = OpenApiResponse(
    OpenApiTypes.ANY,
    examples=[
        OpenApiExample(
            "valid response",
            {
                "id": "0736d0dd-6dd4-48dd-8a3c-586ec8ab61b2",
                "request_id": "string",
                "timestamp": "2022-07-04T14:09:31.618887Z",
                "user": "c1090335-a744-4a46-8712-24b6a45cc553",
                "category": "Fire Simulation",
                "parameters": {},
                "geometry": {},
                "geometry_wkt": "POLYGON ((1 2, 3 4, 5 6, 1 2))",
                "layers": [{
                    "datatype_id": "string",
                    "name": "string",
                    "source": "string",
                    "domain": "string",
                    "info": "string",
                    "info_url": None,
                    "status": "PROCESSING",
                    "message": None,
                }]
            }
        )
    ]
)  # yapf: disable

_on_demand_layer_view_response = OpenApiResponse(
    OpenApiTypes.ANY,
    examples=[
        OpenApiExample(
            "valid response",
            [
                {
                    "key": "1",
                    "category": "Fire Simulation",
                    # "source": "string",
                    # "domain": "string",
                    # "info": "string",
                    # "info_url": None,
                    "requests": [
                        {
                            "key": "1.1",
                            "id": "0736d0dd-6dd4-48dd-8a3c-586ec8ab61b2",
                            "request_id": "string",
                            "title": "string",
                            "timestamp": "022-07-04T14:09:31.618887Z",
                            "user": "9aacbe6f-8ae5-479b-a539-2eac942d2c14",
                            "category": "Fire Simulation",
                            "parameters": {},
                            "geometry": {},
                            "geometry_wkt": "POLYGON ((1 2, 3 4, 5 6, 1 2))",
                            "geometry_features": {
                                "type": "FeatureCollection",
                                "features": [{
                                    "type": "Polygon",
                                    "coordinates": [[[1, 2], [3, 4]]]
                                }]
                            },
                            "layers": [
                                {
                                    "key": "1.1.1",
                                    "datatype_id": "string",
                                    "name": "string",
                                    "source": "string",
                                    "domain": "string",
                                    "feature_string": "value of pixel: {{$.features[0].properties.GRAY_INDEX}}",
                                    "status": "string",
                                    "message": None,
                                    "units": "°C",
                                    "info": None,
                                    "info_url": "url",
                                    "metadata_url": "url",
                                    "legend_url": "url",
                                    "pixel_url": "url",
                                    "timeseries_urls": ["url", "url"],
                                    "urls": [
                                        {
                                            "datetime": ["url1", "url2", "url3"]
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

#########
# views #
#########


@method_decorator(
    extend_schema(responses={status.HTTP_200_OK: _map_request_schema}),
    name="create",
)
class MapRequestViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    """
    viewset for Create/Retrieve/Delete but not Update
    """

    lookup_field = "id"
    lookup_url_kwarg = "map_request_id"

    permission_classes = [IsAuthenticated, IsReadOnlyOrOwner]
    serializer_class = MapRequestSerializer

    DATETIME_INPUT_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
    DATETIME_OUTPUT_FORMAT = "%Y-%m-%dT%H:%M:%S.000Z"

    GATEWAY_URL_PATH = "/api/services/app/Layers/GetLayers"
    GEOSERVER_WMS_URL_PATH = "/geoserver/ermes/wms"
    GEOSERVER_WMTS_URL_PATH = "/geoserver/gwc/service/wmts"
    METADATA_URL_PATH = "/api/data/layers/metadata"

    MAX_GEOSERVER_TIMES = 100  # the maximum timestamps that can be passed to GetTimeSeries at once

    WMS_CRS = "EPSG:4326"
    WMTS_CRS = "EPSG:900913"

    @swagger_fake(MapRequest.objects.none())
    def get_queryset(self):
        """
        return all MapRequests owned by this user / organization
        """
        current_user = self.request.user
        if current_user.organization_name:
            organization_users = UserModel.objects.filter(
                organization_name=current_user.organization_name
            ).active()
            queryset = MapRequest.objects.filter(user__in=organization_users)
        else:
            queryset = current_user.map_requests.all()

        return queryset.prefetch_related("map_request_data_types")

    # TODO: ENSURE create IS AN ATOMIC TRANSACTION TO PREVENT RACE CONDITIONS WHEN SETTING request_id

    def perform_create(self, serializer):
        """
        When a MapRequest is created, publish a corresponding message to 
        RMQ in order to trigger the creation of the MapRequest's data
        """
        map_request = serializer.save()
        map_request.invoke()
        return map_request

    def perform_destroy(self, instance):
        """
        When a MapRequest is destroyed, publish a corresponding message to
        RMQ in order to trigger the destruction of the MapRequest's data
        """
        instance.revoke()
        instance.delete()

    @extend_schema(
        request=None,
        responses={status.HTTP_200_OK: _on_demand_layer_view_response}
    )
    @silk_profile(name='List MapRequests')
    def list(self, request, *args, **kwargs):
        """
        does the normal ListModelMixin stuff to get local MapRequests
        but then merges it w/ the remote (proxy) data
        """

        queryset = self.get_queryset()
        map_requests = {
            map_request_data["request_id"]: map_request_data
            for map_request_data in queryset.values()
        }  # dict of map_request_data keyed by request_id

        geoserver_layer_query_params = urlencode(
            {
                "time": "{time}",
                "layer": "{name}",
                "service": "WMTS",
                "request": "GetTile",
                "version": "1.0.0",
                "transparent": True,
                "tilematrixset": self.WMTS_CRS,
                "tilematrix": self.WMTS_CRS + ":{{z}}",
                "tilecol": "{{x}}",
                "tilerow": "{{y}}",
                "format": "image/png",
            },
            safe="{}",
        )
        geoserver_layer_urls = [
            f"{urljoin(geoserver_api_url, self.GEOSERVER_WMTS_URL_PATH)}?{geoserver_layer_query_params}"
            for geoserver_api_url in settings.SAFERS_GEOSERVER_URLS
        ]

        geoserver_legend_query_params = urlencode(
            {
                "layer": "{name}",
                "service": "WMS",
                "request": "GetLegendGraphic",
                "srs": self.WMS_CRS,
                "width": 512,
                "height": 256,
                "format": "image/png",
                "LEGEND_OPTIONS": "fontsize:80;dpi=72"
            },
            safe="{}",
        )
        geoserver_legend_url = f"{urljoin(settings.SAFERS_GEOSERVER_URL, self.GEOSERVER_WMS_URL_PATH)}?{geoserver_legend_query_params}"

        geoserver_pixel_query_params = urlencode(
            {
                "service": "WMS",
                "version": "1.1.0",
                "request": "GetFeatureInfo",
                "srs": self.WMS_CRS,
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
        geoserver_pixel_url = f"{urljoin(settings.SAFERS_GEOSERVER_URL, self.GEOSERVER_WMS_URL_PATH)}?{geoserver_pixel_query_params}"

        geoserver_timeseries_query_params = urlencode(
            {
                "service": "WMS",
                "version": "1.1.0",
                "request": "GetTimeSeries",
                "srs": self.WMS_CRS,
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
        geoserver_timeseries_url = f"{urljoin(settings.SAFERS_GEOSERVER_URL, self.GEOSERVER_WMS_URL_PATH)}?{geoserver_timeseries_query_params}"

        metadata_url = f"{self.request.build_absolute_uri(self.METADATA_URL_PATH)}/{{metadata_id}}?metadata_format={{metadata_format}}"

        view_serializer = LayerViewSerializer(
            data=request.query_params,
            context={
                "include_map_requests":
                    True,
                "map_request_codes": [
                    f"{RMQ_USER}.{request_id}"
                    for request_id in map_requests.keys()
                ],
            }
        )
        view_serializer.is_valid(raise_exception=True)

        on_demand_layers_data = GATEWAY_CLIENT.get_layers(
            auth=TokenAuthentication(request.auth),
            params=view_serializer.validated_data
        )

        # proxy_details is a dict of dicts: "request_id" followed by "data_type_id"
        # it is passed as context to the serializer below to add links, etc. to the model_serializer data
        proxy_details = defaultdict(dict)
        for group in on_demand_layers_data.get("layerGroups") or []:
            for sub_group in group.get("subGroups") or []:
                for layer in sub_group.get("layers") or []:
                    for detail in layer.get("details") or []:
                        request_id = detail.get("mapRequestCode")
                        map_request = map_requests.get(request_id)
                        if map_request is not None:
                            data_type_id = str(layer["dataTypeId"])
                            proxy_details[request_id].update({
                                data_type_id: {
                                    "units": layer.get("unitOfMeasure"),
                                    "info_url": metadata_url.format(metadata_id=detail.get("metadata_Id"), metadata_format="text"),
                                    "metadata_url": metadata_url.format(metadata_id=detail.get("metadata_Id"), metadata_format="json"),
                                    "legend_url": geoserver_legend_url.format(name=quote_plus(detail["name"])),
                                    "pixel_url": geoserver_pixel_url.format(name=quote_plus(detail["name"])),
                                    "timeseries_urls": [
                                        geoserver_timeseries_url.format(
                                            name=quote_plus(detail["name"]),
                                            time=quote_plus(",".join(timestamps_chunk)),
                                        )
                                        for timestamps_chunk in chunk(detail["timestamps"], self.MAX_GEOSERVER_TIMES)
                                    ] if len(detail.get("timestamps", [])) > 1 else None,
                                    "urls": OrderedDict(
                                            [
                                                (
                                                    timestamp,
                                                    [
                                                    url.format(
                                                        name=quote_plus(detail["name"]),
                                                        time=quote_plus(timestamp),
                                                        bbox=quote_plus(map_request["geometry_buffered_extent_str"]),
                                                    )
                                                    for url in geoserver_layer_urls
                                                    ]
                                                )
                                                for timestamp in map(
                                                    lambda x: datetime.strptime(x, self.DATETIME_INPUT_FORMAT).strftime(self.DATETIME_OUTPUT_FORMAT),
                                                    detail.get("timestamps", [])
                                                )
                                            ]
                                        )
                                }
                            })  # yapf: disable

        model_serializer = self.get_serializer(
            queryset,
            context=dict(
                **self.get_serializer_context(), proxy_details=proxy_details
            ),
            many=True,
        )

        return Response(model_serializer.data, status=status.HTTP_200_OK)
