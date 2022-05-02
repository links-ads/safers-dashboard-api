from copy import deepcopy

from django.conf import settings
from django.contrib.gis.geos import Polygon
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _

from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ParseError, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django_filters import rest_framework as filters

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from safers.core.filters import DefaultFilterSetMixin, SwaggerFilterInspector

from safers.users.permissions import IsRemote

from safers.alerts.models import Alert, AlertGeometry, AlertType
from safers.alerts.serializers import AlertSerializer

_alert_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    example={
        "id": "3a851a61-7f8a-4aa1-ad63-31e61b051a36",
        "type": "UNVALIDATED",
        "timestamp": "2022-04-12T14:29:34Z",
        "status": "string",
        "source": "string",
        "scope": "string",
        "category": "string",
        "event": "string",
        "urgency": "string",
        "severity": "string",
        "certainty": "string",
        "description": "",
        "geometry": {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [1, 2],
                            [3, 4],
                        ]
                    },
                    "properties": {}
                }
            ]
        }
    }
)  # yapf: disable

_alert_list_schema = openapi.Schema(
    type=openapi.TYPE_ARRAY, items=_alert_schema
)


class AlertFilterSet(DefaultFilterSetMixin, filters.FilterSet):
    class Meta:
        model = Alert
        fields = {
            "type",
            "status",
            "source",
            "scope",
            "category",
            "urgency",
            "severity",
            "certainty",
        }

    type = filters.ChoiceFilter(choices=AlertType.choices)
    bbox = filters.Filter(
        method="bbox_method", help_text=_("xmin, ymin, xmax, ymax")
    )
    default_bbox = filters.BooleanFilter(
        initial=True,
        help_text=_(
            "If default_bbox is True and no bbox is provided the user's default_aoi bbox will be used; "
            "If default_bbox is False and no bbox is provided then no bbox filter will be passed to the API"
        )
    )

    def bbox_method(self, queryset, name, value):

        try:
            xmin, ymin, xmax, ymax = list(map(float, value.split(",")))
        except ValueError:
            raise ParseError("invalid bbox string supplied")
        bbox = Polygon.from_bbox((xmin, ymin, xmax, ymax))

        return queryset.filter(geometries__geometry__intersects=bbox)

    def filter_queryset(self, queryset):
        """
        As per the documentation, I am overriding this method in order to perform
        additional filtering to the queryset before it is cached
        """

        # update filters based on default fields

        # TODO: ADD DATE FILTERING

        updated_cleaned_data = deepcopy(self.form.cleaned_data)

        default_bbox = updated_cleaned_data.pop("default_bbox")
        if default_bbox and not updated_cleaned_data.get("bbox"):
            user = self.request.user
            default_bbox = user.default_aoi.geometry.extent
            updated_cleaned_data["bbox"] = ",".join(map(str, default_bbox))

        self.form.cleaned_data = updated_cleaned_data

        return super().filter_queryset(queryset)


@method_decorator(
    swagger_auto_schema(
        responses={status.HTTP_200_OK: _alert_list_schema},
        filter_inspectors=[SwaggerFilterInspector]
    ),
    name="list",
)
@method_decorator(
    swagger_auto_schema(responses={status.HTTP_200_OK: _alert_schema}),
    name="retrieve",
)
@method_decorator(
    swagger_auto_schema(responses={status.HTTP_200_OK: _alert_schema}),
    name="update",
)
@method_decorator(
    swagger_auto_schema(responses={status.HTTP_200_OK: _alert_schema}),
    name="partial_update",
)
@method_decorator(
    swagger_auto_schema(responses={status.HTTP_200_OK: _alert_schema}),
    name="favorite",
)
class AlertViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):

    filter_backends = (filters.DjangoFilterBackend, )
    filterset_class = AlertFilterSet

    lookup_field = "id"
    lookup_url_kwarg = "alert_id"
    permission_classes = [IsAuthenticated, IsRemote]
    serializer_class = AlertSerializer

    def get_queryset(self):
        queryset = Alert.objects.all()
        return queryset.prefetch_related("geometries")

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
