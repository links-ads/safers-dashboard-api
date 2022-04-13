from collections import OrderedDict

from django.db import models
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework_gis import serializers as gis_serializers


class DataLayerSerializer(serializers.Serializer):

    # this isn't a ModelSerializer; it's just used
    # for query_param validation in DataLayerViewSet

    OrderType = models.TextChoices("OrderType", "date -date")
    DateTimeFormats = ["iso-8601", "%Y-%m-%d"]
    ProxyFieldMapping = {
        # fields to pass onto proxy
        "bbox": "Bbox",
        "start": "Start",
        "end": "End",
    }

    bbox = serializers.CharField(required=False)
    start = serializers.DateTimeField(
        input_formats=DateTimeFormats, required=False
    )
    end = serializers.DateTimeField(
        input_formats=DateTimeFormats, required=False
    )
    order = serializers.ChoiceField(choices=OrderType.choices, required=False)
    default_bbox = serializers.BooleanField(
        default=True,
        required=False,
        help_text=_(
            "If default_bbox is True and no bbox is provided the user's default_aoi bbox will be used; "
            "If default_bbox is False and no bbox is provided then no bbox filter will be passed to the API"
        )
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

    # def to_representation(self, instance):
    #     representation = super().to_representation(instance)
    #     return OrderedDict(
    #         (self.FieldMapping[k], v) for k, v in representation.items()
    #     )