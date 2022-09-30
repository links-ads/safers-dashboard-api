from django.utils.translation import gettext_lazy as _

from rest_framework import serializers, ISO_8601
from rest_framework_gis import serializers as gis_serializers

from safers.core.fields import UnderspecifiedDateTimeField

ChatbotDateTimeFormats = [ISO_8601, "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"]


class ChatbotViewSerializer(serializers.Serializer):
    """
    Note that this isn't a ModelSerializer; it's just 
    used for query_param validation in the various Chatbot Views
    """

    ProxyFieldMapping = {
        # fields to pass onto proxy
        "max_result_count": "MaxResultCount",
        "skip_count": "SkipCount",
        "draw": "Draw",
        "search_value": "Search.Value",
        "search_regex": "Search.Regex",
        "order": "Order",
        "start": "StartDate",
        "end": "EndDate",
        "bbox": "bbox",  # bbox will need further processing in View
    }

    max_result_count = serializers.IntegerField(required=False, default=1000)
    skip_count = serializers.IntegerField(required=False)
    draw = serializers.IntegerField(required=False)
    search_value = serializers.CharField(required=False)
    search_regex = serializers.BooleanField(default=False, required=False)

    # order  # no need for ordering chatbot responses on the backend

    start = UnderspecifiedDateTimeField(
        input_formats=ChatbotDateTimeFormats,
        required=False,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    end = UnderspecifiedDateTimeField(
        input_formats=ChatbotDateTimeFormats,
        required=False,
        hour=23,
        minute=59,
        second=59,
        microsecond=999999,
    )

    bbox = serializers.CharField(required=False)

    default_date = serializers.BooleanField(
        default=False,
        required=False,
        help_text=_(
            "If default_date is True and no start/end is provided the default start (now) and end (3 days prior to now) will be used; "
            "If default_date is False and no start/end is provided then no date filter will be passed to the API"
        )
    )
    default_bbox = serializers.BooleanField(
        default=True,
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
