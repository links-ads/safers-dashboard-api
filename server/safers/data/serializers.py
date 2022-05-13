from collections import OrderedDict
from datetime import datetime

from django.db import models
from django.utils.dateparse import parse_datetime
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers, ISO_8601
from rest_framework_gis import serializers as gis_serializers

from safers.core.serializers import ContextVariableDefault

DataLayerSerializerDateTimeFormats = [
    ISO_8601, "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"
]


class DataLayerTimeField(serializers.Field):
    # TODO: COPE WITH TIME RANGES AS PER https://docs.geoserver.org/latest/en/user/services/wms/time.html#wms-time

    def to_representation(self, value):
        # python to json
        return value

    def to_internal_value(self, data):

        parsed_datetime = None
        for format in DataLayerSerializerDateTimeFormats:
            if format == ISO_8601:
                try:
                    parsed_datetime = parse_datetime(data)
                except (ValueError, TypeError):
                    pass
            else:
                try:
                    parsed_datetime = datetime.strptime(data, format)
                except (ValueError, TypeError):
                    pass

        if not parsed_datetime:
            raise serializers.ValidationError("invalid timestamp")

        return parsed_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")


class DataLayerSerializer(serializers.Serializer):
    """
    Note that this isn't a ModelSerializer; it's just being
    used for query_param validation in the DataLayer Views
    """

    OrderType = models.TextChoices("OrderType", "date -date")
    ProxyFieldMapping = {
        # fields to pass onto proxy
        "bbox": "Bbox",
        "start": "Start",
        "end": "End",
    }

    n_layers = serializers.IntegerField(
        default=1,
        required=False,
        help_text=_(
            "The number of recent layers to return for each data type. "
            "It is very unlikely you want to change this value."
        ),
    )

    bbox = serializers.CharField(required=False)

    start = serializers.DateTimeField(
        input_formats=DataLayerSerializerDateTimeFormats, required=False
    )
    end = serializers.DateTimeField(
        input_formats=DataLayerSerializerDateTimeFormats, required=False
    )
    order = serializers.ChoiceField(choices=OrderType.choices, required=False)

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

    def validate_n_layers(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "n_layers must be greater thann 0."
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
