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

    def to_representation(self, value):
        return map(lambda x: round(x, self.precision), value.coords)

    def to_internal_value(self, data):
        try:
            return self.geometry_class(data)
        except TypeError as e:
            raise serializers.ValidationError(str(e))
