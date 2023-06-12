from rest_framework import serializers
from rest_framework_gis import serializers as gis_serializers


class SimplifiedGeometryField(serializers.Field):
    """
    Don't deal w/ rest_framework_gis stuff;
    Just deal w/ a simple array.
    """
    def __init__(self, *args, **kwargs):
        self.precision = kwargs.pop("precision", 12)
        self.geometry_class = kwargs.pop("geometry_class")
        super().__init__(*args, **kwargs)

    def to_internal_value(self, data):
        try:
            return self.geometry_class(data)
        except TypeError as e:
            raise serializers.ValidationError(str(e))

    def to_representation(self, value):
        return map(lambda x: round(x, self.precision), value.coords)


class UnderspecifiedDateTimeField(serializers.DateTimeField):
    """
    resets DataTime according to kwargs
    """
    def __init__(self, *args, **kwargs):

        self.replacements = {
            arg: kwargs.pop(arg)
            for arg in ["year", "month", "day", "hour", "minute", "second", "microsecond"]
            if arg in kwargs
        }  # yapf: disable

        super().__init__(format, *args, **kwargs)

    def to_internal_value(self, value):
        internal_value = super().to_internal_value(value)
        return internal_value.replace(**self.replacements)

    def to_representation(self, value):
        representation = super().to_representation(value)
        return representation.replace(**self.replacements)


class EmptyBooleanField(serializers.BooleanField):
    """
    A BooleanField that _properly_ supports default values.  The standard
    DRF BooleanField initially defaults to False.  This means passing an 
    explicit default value has no effect.  This class gets around that by
    ensuring that missing initial_data is treated as `empty` rather than
    `False`.  This forces default values to be evaluated as per:
    https://github.com/encode/django-rest-framework/blob/d252d22343b9c9688db77b59aa72dabd540bd252/rest_framework/serializers.py#L503
    """
    default_empty_html = serializers.empty
    initial = serializers.empty
