import requests
from collections import OrderedDict
from datetime import datetime, timedelta
from urllib.parse import quote_plus, urlencode, urljoin

from django.conf import settings
from django.contrib.gis import geos
from django.utils import timezone
from django.utils.decorators import method_decorator

from rest_framework import mixins, status, viewsets
from rest_framework.permissions import IsAuthenticated

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from safers.core.decorators import swagger_fake

from safers.data.models import MapRequest
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



#########
# views #
#########

PROXY_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


@method_decorator(
    swagger_auto_schema(responses={status.HTTP_200_OK: _map_request_schema}),
    name="create",
)
@method_decorator(
    swagger_auto_schema(responses={status.HTTP_200_OK: _map_request_schema}),
    name="retrieve",
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
    mixins.RetrieveModelMixin,
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
