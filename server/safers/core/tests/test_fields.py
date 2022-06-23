import pytest
from datetime import datetime

from rest_framework import serializers, ISO_8601
from safers.core.fields import *

from rest_framework import serializers, ISO_8601


def test_underspecified_datetime_field():

    _TestSerializerDateTimeFormats = [
        ISO_8601, "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"
    ]

    class _TestSerializer(serializers.Serializer):

        timestamp_1 = UnderspecifiedDateTimeField(
            input_formats=_TestSerializerDateTimeFormats
        )
        timestamp_2 = UnderspecifiedDateTimeField(
            input_formats=_TestSerializerDateTimeFormats, hour=3
        )
        timestamp_3 = UnderspecifiedDateTimeField(
            input_formats=_TestSerializerDateTimeFormats, hour=6
        )
        timestamp_4 = UnderspecifiedDateTimeField(
            input_formats=_TestSerializerDateTimeFormats, hour=9
        )
        timestamp_5 = UnderspecifiedDateTimeField(
            input_formats=_TestSerializerDateTimeFormats, hour=12
        )

    test_timestamp_1 = datetime(2020, 1, 1, 12)  # should stay 12
    test_timestamp_2 = datetime(2020, 1, 1)  # should set to 3
    test_timestamp_3 = datetime(2020, 1, 1, 3)  # should change to 6
    test_timestamp_4 = "2020-01-01"  # should set to 9
    test_timestamp_5 = "2020-01-01T00:00:00Z"  # should change to 12

    test_serializer = _TestSerializer(
        data={
            "timestamp_1": test_timestamp_1,
            "timestamp_2": test_timestamp_2,
            "timestamp_3": test_timestamp_3,
            "timestamp_4": test_timestamp_4,
            "timestamp_5": test_timestamp_5,
        }
    )
    assert test_serializer.is_valid()

    assert test_serializer.validated_data["timestamp_1"].hour == 12
    assert test_serializer.validated_data["timestamp_2"].hour == 3
    assert test_serializer.validated_data["timestamp_3"].hour == 6
    assert test_serializer.validated_data["timestamp_4"].hour == 9
    assert test_serializer.validated_data["timestamp_5"].hour == 12