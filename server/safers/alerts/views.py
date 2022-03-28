from django.conf import settings
from django.utils.decorators import method_decorator

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from django_filters import rest_framework as filters

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from safers.core.decorators import swagger_fake
from safers.core.filters import BBoxFilterSetMixin
from safers.core.views import CannotDeleteViewSet

from safers.alerts.models import Alert
from safers.alerts.serializers import AlertSerializer

###########
# swagger #
###########

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

###########
# filters #
###########


class AlertFilterSet(BBoxFilterSetMixin, filters.FilterSet):
    class Meta:
        model = Alert
        fields = {}

    geometry__bboverlaps = filters.Filter(method="filter_geometry")
    geometry__bbcontains = filters.Filter(method="filter_geometry")


#########
# views #
#########


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

    filter_backends = (filters.DjangoFilterBackend, )
    filterset_class = AlertFilterSet

    @swagger_fake(Alert.objects.none())
    def get_queryset(self):
        user = self.request.user
        # TODO: GET ALL THE ALERTS THIS USER CAN ACCESS
        return Alert.objects.all()

    @action(detail=True, methods=["post"])
    def favorite(self, request, **kwargs):
        """
        Toggles the favorite status of the specified object
        """
        user = request.user
        obj = self.get_object()

        if obj not in user.favorite_alerts.all():
            max_favorites = settings.SAFERS_MAX_FAVORITE_ALERTS
            if user.favorite_alerts.count() >= max_favorites:
                raise ValidationError(
                    f"cannot have more than {max_favorites} events."
                )
            user.favorite_alerts.add(obj)
        else:
            user.favorite_alerts.remove(obj)

        SerializerClass = self.get_serializer_class()
        serializer = SerializerClass(obj, context=self.get_serializer_context())

        return Response(serializer.data, status=status.HTTP_200_OK)
