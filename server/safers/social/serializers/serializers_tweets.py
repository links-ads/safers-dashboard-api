from django.utils.translation import gettext_lazy as _

from rest_framework import serializers, ISO_8601
from rest_framework_gis import serializers as gis_serializers

from safers.social.models import Tweet, TweetLanguageType, TweetHazardType, TweetInfoType

TweetSerializerDateTimeFormats = [ISO_8601, "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"]


class TweetSerializer(gis_serializers.GeoFeatureModelSerializer):
    class Meta:
        model = Tweet
        fields = (
            "tweet_id",
            "timestamp",
            "text",
            "geometry",
        )
        geo_field = "geometry"
        id_field = False

    geometry = gis_serializers.GeometryField(precision=Tweet.PRECISION)


class TweetViewSerializer(serializers.Serializer):
    """
    Note that this isn't a ModelSerializer; it's just 
    used for query_param validation in TweetView
    """

    ProxyFieldMapping = {
        # fields to pass onto proxy
        "languages": "Languages",
        "hazards": "Hazards",
        "info_types": "Infotypes",
        "start": "Start",
        "end": "End",
        "limit": "Limit",
        "bbox": "bbox",  # bbox will need further processing in View
    }

    languages = serializers.MultipleChoiceField(
        choices=TweetLanguageType.choices,
        default=TweetLanguageType.values,
        required=False,
    )

    hazards = serializers.MultipleChoiceField(
        choices=TweetHazardType.choices,
        default=[TweetHazardType.WILDFIRE],
        required=False,
    )

    info_types = serializers.MultipleChoiceField(
        choices=TweetInfoType.choices,
        required=False,
    )

    limit = serializers.IntegerField(required=False, default=100)

    bbox = serializers.CharField(required=False)

    start = serializers.DateTimeField(
        input_formats=TweetSerializerDateTimeFormats, required=False
    )
    end = serializers.DateTimeField(
        input_formats=TweetSerializerDateTimeFormats, required=False
    )

    default_start = serializers.BooleanField(
        default=True,
        required=False,
        help_text=_(
            "If default_start is True and no start is provided the default start (now) will be used; "
            "If default_start is False and no start is provided then no start filter will be passed to the API"
        )
    )
    default_end = serializers.BooleanField(
        default=True,
        required=False,
        help_text=_(
            "If default_end is True and no end is provided the default start (3 days prior to now) will be used; "
            "If default_end is False and no end is provided then no end filter will be passed to the API"
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