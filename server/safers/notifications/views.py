from copy import deepcopy

from django.conf import settings
from django.contrib.gis.geos import Polygon
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _

from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ParseError
from rest_framework.generics import get_object_or_404 as drf_get_object_or_404
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from django_filters import rest_framework as filters

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from safers.core.decorators import swagger_fake
from safers.core.filters import DefaultFilterSetMixin, SwaggerFilterInspector, CaseInsensitiveChoiceFilter

from safers.users.permissions import IsRemote

from safers.notifications.models import Notification, NotificationSourceChoices, NotificationTypeChoices, NotificationScopeChoices, NotificationRestrictionChoices
from safers.notifications.serializers import NotificationSerializer


_notification_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    example={
        "id": "db9634fc-ae64-44bf-ba31-7abf4f68daa9",
        "title": "Notification db9634c [Met]",
        "type": "RECOMMENDATION",
        "timestamp": "2022-04-28T11:38:28Z",
        "status": "Actual",
        "source": "EFFIS_FWI",
        "scope": "Public",
        "restriction": None,
        "target_organizations": [],
        "scopeRestriction": "Public",
        "category": "Met",
        "event": "Probability of fire",
        "description": "Do not light open-air barbecues in forest.",
        "geometry": {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [1, 2],
                            [3, 4]
                        ]
                    },
                    "properties": {
                        "description": "areaDesc"
                    }
                }
            ]
        },
        "center": [1, 2],
        "bounding_box": [1, 2, 3, 4]
    }
)  # yapf: disable


_notification_list_schema = openapi.Schema(
    type=openapi.TYPE_ARRAY, items=_notification_schema
)


class NotificationFilterSet(DefaultFilterSetMixin, filters.FilterSet):
    class Meta:
        model = Notification
        fields = {
            "status",
            "source",
            "type",
            "scope",
            "restriction",
            "category",
            "event",
        }

    order = filters.OrderingFilter(fields=(("timestamp", "date"), ))

    source = CaseInsensitiveChoiceFilter(
        choices=NotificationSourceChoices.choices
    )
    type = CaseInsensitiveChoiceFilter(choices=NotificationTypeChoices.choices)
    scope = CaseInsensitiveChoiceFilter(
        choices=NotificationScopeChoices.choices
    )
    restriction = CaseInsensitiveChoiceFilter(
        choices=NotificationRestrictionChoices.choices
    )

    scopeRestriction = CaseInsensitiveChoiceFilter(
        choices=[
            (
                NotificationScopeChoices.PUBLIC.value,
                NotificationScopeChoices.PUBLIC.label
            ),
        ] + NotificationRestrictionChoices.choices,
        method="get_scope_restriction"
    )
    start_date = filters.DateTimeFilter(
        field_name="timestamp", lookup_expr="date__gte"
    )
    end_date = filters.DateTimeFilter(
        field_name="timestamp", lookup_expr="date__lte"
    )
    default_date = filters.BooleanFilter(
        initial=False,
        help_text=_(
            "If default_date is True and no end_date is provided then the current date will be used and if no start_date is provided then 3 days previous will be used; "
            "If default_date is False and no end_date or start_date is used then no date filters will be passed to the API."
        )
    )
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

    def get_scope_restriction(self, queryset, name, value):
        if value in NotificationScopeChoices:
            return queryset.filter(scope=value)
        elif value in NotificationRestrictionChoices:
            return queryset.filter(restriction=value)
        return queryset

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

        # update filters based on default values

        updated_cleaned_data = deepcopy(self.form.cleaned_data)

        default_bbox = updated_cleaned_data.pop("default_bbox")
        if default_bbox and not updated_cleaned_data.get("bbox"):
            user = self.request.user
            bbox = user.default_aoi.geometry.extent
            updated_cleaned_data["bbox"] = ",".join(map(str, bbox))

        default_date = updated_cleaned_data.pop("default_date")
        if default_date and not updated_cleaned_data.get("end_date"):
            updated_cleaned_data["end_date"] = timezone.now()
        if default_date and not updated_cleaned_data.get("start_date"):
            updated_cleaned_data["start_date"] = timezone.now(
            ) - settings.SAFERS_DEFAULT_TIMERANGE

        self.form.cleaned_data = updated_cleaned_data

        return super().filter_queryset(queryset)


@method_decorator(
    swagger_auto_schema(
        responses={status.HTTP_200_OK: _notification_list_schema},
        filter_inspectors=[SwaggerFilterInspector]
    ),
    name="list",
)
@method_decorator(
    swagger_auto_schema(
        responses={status.HTTP_200_OK: _notification_list_schema},
    ),
    name="retrieve",
)
class NotificationViewSet(viewsets.ReadOnlyModelViewSet):

    filter_backends = (filters.DjangoFilterBackend, )
    filterset_class = NotificationFilterSet

    lookup_field = "id"
    lookup_url_kwarg = "notification_id"
    permission_classes = [IsAuthenticated, IsRemote]
    serializer_class = NotificationSerializer

    @swagger_fake(Notification.objects.none())
    def get_queryset(self):
        queryset = Notification.objects.filter_by_user(self.request.user)
        return queryset.prefetch_related("geometries")

    def get_object(self):
        queryset = self.get_queryset()

        # disable filtering for detail views
        # (the rest of this fn is just like the parent class)
        # TODO: https://github.com/astrosat/safers-dashboard-api/issues/45
        if self.action in ["list"]:
            queryset = self.filter_queryset(queryset)

        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        obj = drf_get_object_or_404(queryset, **filter_kwargs)

        self.check_object_permissions(self.request, obj)

        return obj


@swagger_auto_schema(
    responses={
        status.HTTP_200_OK:
            openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_STRING)
            )
    },
    method="get"
)
@api_view(["GET"])
@permission_classes([AllowAny])
def notification_sources_view(request):
    """
    Returns the list of possible notification sources.
    """
    return Response(NotificationSourceChoices.values, status=status.HTTP_200_OK)


@swagger_auto_schema(
    responses={
        status.HTTP_200_OK:
            openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_STRING)
            )
    },
    method="get"
)
@api_view(["GET"])
@permission_classes([AllowAny])
def notification_types_view(request):
    """
    Returns the list of possible notification types.
    """
    return Response(NotificationTypeChoices.values, status=status.HTTP_200_OK)


@swagger_auto_schema(
    responses={
        status.HTTP_200_OK:
            openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_STRING)
            )
    },
    method="get"
)
@api_view(["GET"])
@permission_classes([AllowAny])
def notification_scopes_restrictions_view(request):
    """
    Returns the list of possible notification scope/restriction types.
    """
    scopes = [
        NotificationScopeChoices.PUBLIC,
    ]  # no need to include "Restricted" scope
    restrictions = NotificationRestrictionChoices.values
    return Response(scopes + restrictions, status=status.HTTP_200_OK)
