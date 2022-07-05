from collections import OrderedDict

from django.utils.decorators import method_decorator

from rest_framework import mixins, status, viewsets
from rest_framework.permissions import IsAuthenticated

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from safers.core.decorators import swagger_fake

from safers.data.models import MapRequest
from safers.data.serializers import MapRequestSerializer

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
        "status": "PROCESSING",
        "category": "Post Event Monitoring",
        "parameters": {},
        "geometry": None,
        "data_types": ["a", "b", "c"],
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
            ("children", openapi.Schema(type=openapi.TYPE_ARRAY, items=_map_request_schema)),
        ))
    )
)  # yapf: disable

#########
# views #
#########


@method_decorator(
    swagger_auto_schema(
        responses={status.HTTP_200_OK: _map_request_list_schema},
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
        return current_user.map_requests.prefetch_related("data_types").all()
