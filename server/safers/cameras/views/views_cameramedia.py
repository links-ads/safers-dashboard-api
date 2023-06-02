from django.conf import settings
from django.contrib.gis.geos import Polygon
from django.db.models import BooleanField, ExpressionWrapper, Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import ParseError, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from django_filters import rest_framework as filters

from drf_spectacular.utils import extend_schema, extend_schema_field, extend_schema_view, OpenApiExample, OpenApiResponse, OpenApiTypes, OpenApiParameter

from safers.core.decorators import swagger_fake
from safers.core.filters import CaseInsensitiveChoiceFilter, CharInFilter, DefaultFilterSetMixin, MultiFieldOrderingFilter, SwaggerFilterInspector

from safers.cameras.models import Camera, CameraMedia, CameraMediaType, CameraMediaFireClass, CameraMediaTag
from safers.cameras.serializers import CameraMediaSerializer


class CameraMediaFilterSet(DefaultFilterSetMixin, filters.FilterSet):
    class Meta:
        model = CameraMedia
        fields = {
            "type",
        }

    # TODO: MULTIPLE CHOICES ALLOWED IN SWAGGER
    order = MultiFieldOrderingFilter(
        fields=(("timestamp", "date"), ), multi_fields=["-favorite"]
    )

    type = CaseInsensitiveChoiceFilter(choices=CameraMediaType.choices)

    # TODO: RENDER CHOICES IN SWAGGER
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
        initial=False,
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

        default_date = self.form.cleaned_data.pop("default_date")
        if default_date and not self.form.cleaned_data.get("end_date"):
            self.form.cleaned_data["end_date"] = timezone.now()
        if default_date and not self.form.cleaned_data.get("start_date"):
            self.form.cleaned_data["start_date"] = timezone.now(
            ) - settings.SAFERS_DEFAULT_TIMERANGE

        default_bbox = self.form.cleaned_data.pop("default_bbox")
        if default_bbox and not self.form.cleaned_data.get("bbox"):
            user = self.request.user
            bbox = user.default_aoi.geometry.extent
            self.form.cleaned_data["bbox"] = ",".join(map(str, bbox))

        return super().filter_queryset(queryset)


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

    @swagger_fake(CameraMedia.objects.none())
    def get_queryset(self):
        """
        ensures that favorite camera_medias are at the start of the qs
        """
        qs = CameraMedia.objects.active(
        ).select_related("camera").prefetch_related("tags", "fire_classes")

        user = self.request.user
        favorite_camera_meda_ids = user.favorite_camera_medias.values_list(
            "id", flat=True
        )
        qs = qs.annotate(
            favorite=ExpressionWrapper(
                Q(id__in=favorite_camera_meda_ids),
                output_field=BooleanField(),
            )
        )
        return qs.order_by("-favorite")

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


@extend_schema(
    request=None,
    responses={
        status.HTTP_200_OK:
            OpenApiResponse(
                OpenApiTypes.ANY,
                examples=[OpenApiExample(
                    "valid response",
                    ["string"],
                )]
            )
    }
)
@api_view(["GET"])
@permission_classes([AllowAny])
def camera_media_sources_view(request):
    """
    Returns the list of possible cameras to use as sources.
    """
    cameras = Camera.objects.active()
    return Response(
        cameras.values_list("camera_id", flat=True), status=status.HTTP_200_OK
    )
