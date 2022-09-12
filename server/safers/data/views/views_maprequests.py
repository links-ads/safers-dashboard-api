import requests
from collections import OrderedDict, defaultdict
from urllib.parse import quote_plus, urlencode, urljoin

from django.conf import settings
from django.utils.decorators import method_decorator

from rest_framework import mixins, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from safers.core.decorators import swagger_fake

from safers.data.models import MapRequest, DataType
from safers.data.serializers import MapRequestSerializer, MapRequestViewSerializer

from safers.users.authentication import ProxyAuthentication
from safers.users.exceptions import AuthenticationException
from safers.users.permissions import IsRemote

###########
# swagger #
###########

_map_request_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    example={
        "key": "1.1",
        "id": "0736d0dd-6dd4-48dd-8a3c-586ec8ab61b2",
        "request_id": "string",
        "timestamp": "2022-07-04T14:09:31.618887Z",
        "category": "Post Event Monitoring",
        "parameters": {},
        "geometry": None,
        "layers": [
            {
                "key": "1.1.1",
                "status": "PROCESSING",
                "url": "whatever",
            }
        ]
    }
)  # yapf: disable

_map_request_list_schema = openapi.Schema(
    type=openapi.TYPE_ARRAY,
    items=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties=OrderedDict((
            ("key", openapi.Schema(type=openapi.TYPE_STRING, example="1")),
            ("category", openapi.Schema(type=openapi.TYPE_STRING, example="Post Event Monitoring")),
            # TODO: REPLACE _map_request_schema w/ MapRequestSerializer (as per https://github.com/axnsan12/drf-yasg/issues/88)
            ("requests", openapi.Schema(type=openapi.TYPE_ARRAY, items=_map_request_schema)),
        ))
    )
)  # yapf: disable



_map_request_sources_schema = openapi.Schema(
    type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)
)  # yapf: disable


_map_request_domains_schema = openapi.Schema(
    type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)
)  # yapf: disable


#########
# views #
#########


@method_decorator(
    swagger_auto_schema(responses={status.HTTP_200_OK: _map_request_schema}),
    name="create",
)
@method_decorator(
    swagger_auto_schema(
        responses={status.HTTP_200_OK: _map_request_list_schema}
    ),
    name="list",
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

    permission_classes = [IsAuthenticated, IsRemote]
    serializer_class = MapRequestSerializer

    @swagger_fake(MapRequest.objects.none())
    def get_queryset(self):
        """
        return all MapRequests owned by this user
        """
        current_user = self.request.user
        return current_user.map_requests.prefetch_related(
            "map_request_data_types"
        ).all()

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

    @swagger_auto_schema(
        query_serializer=MapRequestViewSerializer,
        #     # responses={status.HTTP_200_OK: _data_layer_list_schema}
    )
    def list(self, request, *args, **kwargs):
        """
        does the normal ListModelMixin stuff to get local MapRequests
        but then merges it w/ the remote (proxy) data
        """

        GATEWAY_URL_PATH = "/api/services/app/Layers/GetLayers"
        GEOSERVER_URL_PATH = "/geoserver/ermes/wms"
        METADATA_URL_PATH = "/api/data/layers/metadata"

        geoserver_layer_query_params = urlencode(
            {
                "time": "{time}",
                "layers": "{name}",
                "service": "WMS",
                "request": "GetMap",
                "srs": "EPSG:4326",
                "bbox": "{{bbox}}",
                "transparent": True,
                "width": 256,
                "height": 256,
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

        queryset = self.get_queryset()
        map_request_ids = queryset.values_list("request_id", flat=True)

        view_serializer = MapRequestViewSerializer(
            data=request.query_params,
            context=self.get_serializer_context(),
        )
        view_serializer.is_valid(raise_exception=True)

        proxy_params = {
            view_serializer.ProxyFieldMapping[k]: v
            for k, v in view_serializer.validated_data.items()
            if k in view_serializer.ProxyFieldMapping
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

        proxy_content = response.json()

        # can't figure out how to do this in a list comprehension
        # proxy_details = [
        #     detail for group in proxy_content.get("layerGroups", [])
        #     for sub_group in group.get("subGroups", [])
        #     for layer in sub_group.get("layers", [])
        #     for detail in layer.get("details", [])
        #     if detail.get("mapRequestCode") in map_request_ids
        # ]

        # proxy_details is a dict of dicts: "request_id" followed by "data_type_id"
        # it is passed as context to the serializer below to add links, etc. to the model_serializer data
        proxy_details = defaultdict(dict)
        for group in proxy_content.get("layerGroups", []):
            for sub_group in group.get("subGroups", []):
                for layer in sub_group.get("layers", []):
                    for detail in layer.get("details", []):
                        request_id = detail.get("mapRequestCode")
                        if request_id in map_request_ids:
                            # yapf: disable
                            proxy_details[request_id].update({
                                str(layer["dataTypeId"]): {
                                    "info": None,
                                    "info_url": metadata_url.format(metadata_id=detail.get("metadata_Id"), metadata_format="text"),
                                    "metadata_url": metadata_url.format(metadata_id=detail.get("metadata_Id"), metadata_format="json"),
                                    "legend_url": geoserver_legend_url.format(name=quote_plus(detail["name"])),
                                    "pixel_url": geoserver_pixel_url.format(name=quote_plus(detail["name"])),
                                    "timeseries_url":
                                        geoserver_timeseries_url.format(
                                            name=quote_plus(detail["name"]),
                                            time=quote_plus(",".join(detail["timestamps"])),
                                        )
                                        if len(detail.get("timestamps", [])) > 0
                                        else None,
                                    "urls": [
                                        OrderedDict(
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
                                    ]
                                }
                            })


        model_serializer = self.get_serializer(
            queryset,
            context=dict(
                **self.get_serializer_context(), proxy_details=proxy_details
            ),
            many=True,
        )

        return Response(model_serializer.data, status=status.HTTP_200_OK)




@swagger_auto_schema(
    responses={status.HTTP_200_OK: _map_request_domains_schema}, method="get"
)
@api_view(["GET"])
@permission_classes([AllowAny])
def map_request_domains_view(request):
    """
    Returns the list of possible MapRequest domains.
    """
    data_type_domains = DataType.objects.on_demand().only("domain").exclude(
        domain__isnull=True
    ).order_by("domain").values_list("domain", flat=True).distinct()
    return Response(data_type_domains, status=status.HTTP_200_OK)


@swagger_auto_schema(
    responses={status.HTTP_200_OK: _map_request_sources_schema}, method="get"
)
@api_view(["GET"])
@permission_classes([AllowAny])
def map_request_sources_view(request):
    """
    Returns the list of possible MapRequest sources.
    """
    data_type_sources = DataType.objects.on_demand().only("source").exclude(
        source__isnull=True
    ).order_by("source").values_list("source", flat=True).distinct()
    return Response(data_type_sources, status=status.HTTP_200_OK)
