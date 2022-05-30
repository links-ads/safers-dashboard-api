from django.utils.translation import gettext_lazy as _

from rest_framework import serializers, ISO_8601
from rest_framework_gis import serializers as gis_serializers

from safers.chatbot.models import Report, ReportHazardTypes, ReportStatusTypes, ReportContentTypes, ReportVisabilityTypes

ReportSerializerDateTimeFormats = [ISO_8601, "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"]

# class ReportMediaSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ReportMedia
#         fields = (
#             "type",
#             "url",
#             "thumbnail",
#         )


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = (
            "name",
            "report_id",
            "mission_id",
            "timestamp",
            "source",
            "hazard",
            "status",
            "content",
            "visibility",
            "description",
            "reporter",
            "media",
            "geometry",
            "location",
        )

    # media = ReportMediaSerializer(many=True)

    geometry = gis_serializers.GeometryField(
        precision=Report.PRECISION, remove_duplicates=True
    )

    location = serializers.SerializerMethodField()

    def get_location(self, obj):
        if obj.geometry:
            return obj.geometry.coords


class ReportViewSerializer(serializers.Serializer):
    """
    Note that this isn't a ModelSerializer; it's just 
    used for query_param validation in ReportView
    """

    ProxyFieldMapping = {
        # fields to pass onto proxy
        # "hazards": "Hazards",
        # "status": "Status",
        # "content": "Contents",
        "visibility": "Visibility",
        "start": "StartDate",
        "end": "EndDate",
        "max_results": "MaxResultCount",
        "bbox": "bbox",  # bbox will need further processing in View
    }

    hazards = serializers.MultipleChoiceField(
        choices=ReportHazardTypes.choices,
        default=[ReportHazardTypes.FIRE],  # required=False,
    )

    status = serializers.MultipleChoiceField(
        choices=ReportStatusTypes.choices,
        default=[
            ReportStatusTypes.UNKNOWN,
            ReportStatusTypes.NOTIFIED,
            ReportStatusTypes.MANAGED,
        ],
        required=False,
    )

    content = serializers.MultipleChoiceField(
        choices=ReportContentTypes.choices,
        required=False,
    )

    visibility = serializers.ChoiceField(
        choices=ReportVisabilityTypes.choices,
        default=ReportVisabilityTypes.ALL.value,
        required=False,
    )

    max_results = serializers.IntegerField(required=False, default=1000)

    bbox = serializers.CharField(required=False)

    start = serializers.DateTimeField(
        input_formats=ReportSerializerDateTimeFormats, required=False
    )
    end = serializers.DateTimeField(
        input_formats=ReportSerializerDateTimeFormats, required=False
    )

    default_start = serializers.BooleanField(
        # default=True,
        default=False,
        required=False,
        help_text=_(
            "If default_start is True and no start is provided the default start (now) will be used; "
            "If default_start is False and no start is provided then no start filter will be passed to the API"
        )
    )
    default_end = serializers.BooleanField(
        # default=True,
        default=False,
        required=False,
        help_text=_(
            "If default_end is True and no end is provided the default start (3 days prior to now) will be used; "
            "If default_end is False and no end is provided then no end filter will be passed to the API"
        )
    )
    default_bbox = serializers.BooleanField(
        # default=True,
        default=False,
        required=False,
        help_text=_(
            "If default_bbox is True and no bbox is provided the user's default_aoi bbox will be used; "
            "If default_bbox is False and no bbox is provided then no bbox filter will be passed to the API"
        )
    )

    def validate_max_results(self, value):
        if value <= 0 or value > 1000:
            raise serializers.ValidationError(
                "max_results must be between 1 and 1000"
            )
        return value

    def validate_bbox(self, value):
        try:
            bbox = list(map(float, value.split(",")))
            assert len(bbox) == 4, "bbox must contain 4 values"
        except Exception as e:
            raise serializers.ValidationError(e)
        return bbox

    def validate(self, data):

        validated_data = super().validate(data)

        # check timestamps...
        start = validated_data.get("start")
        end = validated_data.get("end")
        if start and end and start >= end:
            raise serializers.ValidationError("end must occur after start")

        return validated_data