from copy import deepcopy
from functools import reduce
from operator import __or__

from django.conf import settings
from django.contrib.gis.geos import Polygon
from django.db.models import BooleanField, ExpressionWrapper, Q
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _

from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import ParseError, ValidationError
from rest_framework.generics import get_object_or_404 as drf_get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from django_filters import rest_framework as filters

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema, no_body

from safers.core.filters import CaseInsensitiveChoiceFilter, CharInFilter, DefaultFilterSetMixin, MultiFieldOrderingFilter, SwaggerFilterInspector

from safers.users.permissions import IsLocal, IsRemote

from safers.cameras.models import Camera, CameraMedia, CameraMediaType, CameraMediaFireClass, CameraMediaTag
from safers.cameras.serializers import CameraMediaSerializer

_camera_media_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    example={
        "id": "4b9f28a9-8d70-4d62-914e-1bb64da07908",
        "timestamp": "2022-01-27T08:48:00Z",
        "description": None,
        "camera_id":  "PCF_El_Perello_297",
        "type":  "IMAGE",
        "fire_classes": ["C1"],
        "tags": ["fire"],
        "direction": 1,
        "distance": 2,
        "geometry": {},
        "url": "https://s3.eu-central-1.amazonaws.com/waterview.faketp/PCFElPerello_1db3454c2250/2022/05/19/pic_2022-05-19_08-22-40.jpg?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAJQR7EL2CSUT7FDIA%2F20220519%2Feu-central-1%2Fs3%2Faws4_request&X-Amz-Date=20220519T082248Z&X-Amz-Expires=1200&X-Amz-SignedHeaders=host&X-Amz-Signature=e7e68343d43abaa7bb0771c50bb180e7b7ac0bd11c3aeaf433a8f2c8a90b0a86",
        "favorite": False,
    }
)  # yapf: disable


_camera_media_list_schema = openapi.Schema(
    type=openapi.TYPE_ARRAY, items=_camera_media_schema
)


class CameraMediaFilterSet(DefaultFilterSetMixin, filters.FilterSet):
    class Meta:
        model = CameraMedia
        fields = {
            "type",
        }

    order = MultiFieldOrderingFilter(
        fields=(("timestamp", "date"), ), multi_fields=["favorite"]
    )

    type = CaseInsensitiveChoiceFilter(choices=CameraMediaType.choices)

    camera_id = filters.ModelChoiceFilter(
        field_name="camera",
        lookup_expr="exact",  # not sure why I can't use "iexact" ?
        queryset=Camera.objects.all(),
        to_field_name="camera_id",
        help_text=_("The id of the camera that created the media")
    )

    tags = CharInFilter(
        # not using MultipleModelChoiceFilter b/c I want to allow a comma-separated list of values
        field_name="tags__name",
        lookup_expr="in",
        help_text=_("How this media has been taged (ie: 'smoke','fire')")
    )

    start_date = filters.DateFilter(
        field_name="timestamp", lookup_expr="date__gte"
    )
    end_date = filters.DateFilter(
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
        method="bbox_filter", help_text=_("xmin, ymin, xmax, ymax")
    )
    default_bbox = filters.BooleanFilter(
        initial=True,
        help_text=_(
            "If default_bbox is True and no bbox is provided the user's default_aoi bbox will be used; "
            "If default_bbox is False and no bbox is provided then no bbox filter will be passed to the API"
        )
    )

    def bbox_filter(self, queryset, name, value):

        try:
            xmin, ymin, xmax, ymax = list(map(float, value.split(",")))
        except ValueError:
            raise ParseError("invalid bbox string supplied")
        bbox = Polygon.from_bbox((xmin, ymin, xmax, ymax))

        return queryset.filter(camera__geometry__intersects=bbox)

    def filter_queryset(self, queryset):
        """
        As per the documentation, I am overriding this method in order to perform
        additional filtering to the queryset before it is cached
        """

        # update filters based on default fields

        updated_cleaned_data = deepcopy(self.form.cleaned_data)

        default_date = updated_cleaned_data.pop("default_date")
        if default_date and not updated_cleaned_data.get("end_date"):
            updated_cleaned_data["end_date"] = timezone.now()
        if default_date and not updated_cleaned_data.get("start_date"):
            updated_cleaned_data["start_date"] = timezone.now(
            ) - settings.SAFERS_DEFAULT_TIMERANGE

        default_bbox = updated_cleaned_data.pop("default_bbox")
        if default_bbox and not updated_cleaned_data.get("bbox"):
            user = self.request.user
            bbox = user.default_aoi.geometry.extent
            updated_cleaned_data["bbox"] = ",".join(map(str, bbox))

        self.form.cleaned_data = updated_cleaned_data

        return super().filter_queryset(queryset)


@method_decorator(
    swagger_auto_schema(
        responses={status.HTTP_200_OK: _camera_media_list_schema},
        filter_inspectors=[SwaggerFilterInspector]
    ),
    name="list",
)
@method_decorator(
    swagger_auto_schema(responses={status.HTTP_200_OK: _camera_media_schema}),
    name="retrieve",
)
@method_decorator(
    swagger_auto_schema(responses={status.HTTP_200_OK: _camera_media_schema}),
    name="update",
)
@method_decorator(
    swagger_auto_schema(responses={status.HTTP_200_OK: _camera_media_schema}),
    name="partial_update",
)
@method_decorator(
    swagger_auto_schema(
        responses={status.HTTP_200_OK: _camera_media_schema},
        request_body=no_body,
    ),
    name="favorite",
)
class CameraMediaViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet
):

    filter_backends = (filters.DjangoFilterBackend, )
    filterset_class = CameraMediaFilterSet

    lookup_field = "id"
    lookup_url_kwarg = "camera_media_id"
    permission_classes = [IsAuthenticated]
    serializer_class = CameraMediaSerializer

    def get_queryset(self):
        """
        ensures that favorite camera_medias are at the start of the qs
        """
        user = self.request.user
        qs = CameraMedia.objects.all().prefetch_related(
            "fire_classes", "favorited_users"
        )
        qs = qs.annotate(
            favorite=ExpressionWrapper(
                Q(favorited_users=user), output_field=BooleanField()
            )
        ).distinct()
        return qs.order_by("favorite")

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

    @action(detail=True, methods=["post"])
    def favorite(self, request, **kwargs):
        """
        Toggles the favorite status of the specified object
        """
        user = request.user
        obj = self.get_object()

        if obj not in user.favorite_camera_medias.all():
            max_favorites = settings.SAFERS_MAX_FAVORITE_CAMERA_MEDIA
            if user.favorite_camera_medias.count() >= max_favorites:
                raise ValidationError(
                    f"cannot have more than {max_favorites} camera_media."
                )
            user.favorite_camera_medias.add(obj)
        else:
            user.favorite_camera_medias.remove(obj)

        SerializerClass = self.get_serializer_class()
        serializer = SerializerClass(obj, context=self.get_serializer_context())

        return Response(serializer.data, status=status.HTTP_200_OK)


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
def camera_media_sources_view(request):
    """
    Returns the list of possible cameras to use as sources.
    """
    cameras = Camera.objects.all()
    return Response(
        cameras.values_list("camera_id", flat=True), status=status.HTTP_200_OK
    )
