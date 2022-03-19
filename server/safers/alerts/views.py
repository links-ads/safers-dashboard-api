from django.conf import settings
from django.utils.decorators import method_decorator

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from safers.core.decorators import swagger_fake
from safers.core.views import CannotDeleteViewSet

from safers.alerts.models import Alert
from safers.alerts.serializers import AlertSerializer

_alert_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    example={
        "id": "9953b183-5f18-41b1-ac96-23121ac33de7",
        "timestamp": "2022-03-19T10:01:04Z",
        "description": "string",
        "source": "string",
        "status": "UNVALIDATED",
        "media": [
            "http://some.image.com",
            "http://another.image.com"
        ],
        "geometry": {
            "type": "Polygon",
            "coordinates": [[1,2],[3,4]]
        },
        "bounding_box": {
            "type": "Polygon",
            "coordinates": [[1,2],[3,4]]
        }
    }
)  # yapf: disable

_alert_list_schema = openapi.Schema(
    type=openapi.TYPE_ARRAY, items=_alert_schema
)


@method_decorator(
    swagger_auto_schema(responses={status.HTTP_200_OK: _alert_list_schema}),
    name="list",
)
@method_decorator(
    swagger_auto_schema(responses={status.HTTP_200_OK: _alert_schema}),
    name="create",
)
@method_decorator(
    swagger_auto_schema(responses={status.HTTP_200_OK: _alert_schema}),
    name="retrieve",
)
@method_decorator(
    swagger_auto_schema(responses={status.HTTP_200_OK: _alert_schema}),
    name="update",
)
class AlertViewSet(CannotDeleteViewSet):
    # permission_classes = [TODO: SOME KIND OF FACTORY FUNCTION HERE]
    serializer_class = AlertSerializer
    lookup_field = "id"
    lookup_url_kwarg = "alert_id"

    @swagger_fake(Alert.objects.none())
    def get_queryset(self):
        user = self.request.user
        # TODO: GET ALL THE ALERTS THIS USER CAN ACCESS
        return Alert.objects.all()

    # TODO: NOT SURE IF I SHOULD HAVE A SEPARATE ACTION HERE
    # TODO: OR JUST USE A PUT REQUEST TO THE USERS API
    @action(detail=True, methods=["post"])
    def favorite(self, request, pk=None):
        user = request.user
        aoi = self.get_object()

        max_favorite_alerts = settings.SAFERS_MAX_FAVORITE_ALERTS
        if user.favorite_alerts.count() >= max_favorite_alerts:
            return Response(
                data={
                    "error":
                        f"{user} cannot have more than {max_favorite_alerts} alerts."
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        user.favorite_alerts.add(aoi)

        return Response(
            data={"detail": f"{user} favorited {aoi}."},
            status=status.HTTP_200_SUCCESS,
        )
