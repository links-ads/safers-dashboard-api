from copy import deepcopy

from django.conf import settings
from django.contrib.gis.geos import Polygon
from django.utils.translation import gettext_lazy as _

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ParseError, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django_filters import rest_framework as filters

from safers.core.filters import DefaultFilterSetMixin

from safers.users.permissions import IsRemote

from safers.notifications.models import Notification
from safers.notifications.serializers import NotificationSerializer


class NotificationFilterSet(DefaultFilterSetMixin, filters.FilterSet):
    class Meta:
        model = Notification
        fields = {
            "status",
            "source",
            "scope",
            "category",
            "event",
            "urgency",
            "severity",
            "certainty",
        }

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

        # update filters based on default values
        updated_cleaned_data = deepcopy(self.form.cleaned_data)
        if updated_cleaned_data.pop("default_bbox"
                                   ) and not updated_cleaned_data.get("bbox"):
            user = self.request.user
            default_bbox = user.default_aoi.geometry.extent
            updated_cleaned_data["bbox"] = ",".join(map(str, default_bbox))

        self.form.cleaned_data = updated_cleaned_data

        return super().filter_queryset(queryset)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):

    filter_backends = (filters.DjangoFilterBackend, )
    filterset_class = NotificationFilterSet

    lookup_field = "id"
    lookup_url_kwarg = "notification_id"
    permission_classes = [IsAuthenticated, IsRemote]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        queryset = Notification.objects.all()
        return queryset.prefetch_related("geometries")

    # @action(detail=True, methods=["post"])
    # def favorite(self, request, **kwargs):
    #     """
    #     Toggles the favorite status of the specified object
    #     """
    #     user = request.user
    #     obj = self.get_object()

    #     if obj not in user.favorite_notifications.all():
    #         max_favorites = settings.SAFERS_MAX_NOTIFICATIONS
    #         if user.favorite_notifications.count() >= max_favorites:
    #             raise ValidationError(
    #                 f"cannot have more than {max_favorites} notifications."
    #             )
    #         user.favorite_notifications.add(obj)
    #     else:
    #         user.favorite_notifications.remove(obj)

    #     SerializerClass = self.get_serializer_class()
    #     serializer = SerializerClass(obj, context=self.get_serializer_context())

    #     return Response(serializer.data, status=status.HTTP_200_OK)
