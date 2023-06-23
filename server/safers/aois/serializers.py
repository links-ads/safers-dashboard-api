from collections import OrderedDict

from django.contrib.gis.geos import Point

from rest_framework import serializers
from rest_framework_gis import serializers as gis_serializers

from drf_spectacular.utils import extend_schema_serializer, OpenApiExample

from safers.core.fields import SimplifiedGeometryField

from safers.aois.models import Aoi


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "valid responese",
            {
                "type": "FeatureCollection",
                "features": [{
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [1, 2],
                            [3, 4],
                        ]
                    },
                    "properties": {
                        "id": 1,
                        "name": "string",
                        "description": "string",
                        "country": "string",
                        "zoomLevel": 0,
                        "midPoint": [1, 2]
                    }
                }]
            },
            response_only=True,
        )
    ]
)  # yapf: disable
class AoiSerializer(gis_serializers.GeoFeatureModelSerializer):
    class Meta:
        model = Aoi
        fields = (
            "id",
            "name",
            "description",
            "country",
            "zoomLevel",
            "midPoint",
            "geometry",
        )

        auto_bbox = True
        id_field = False
        geo_field = "geometry"
        list_serializer_class = serializers.ListSerializer  # don't combine multiple AOIs into a FeatureCollection

    zoomLevel = serializers.FloatField(source="zoom_level")

    midPoint = SimplifiedGeometryField(
        precision=Aoi.PRECISION, geometry_class=Point, source="midpoint"
    )

    geometry = gis_serializers.GeometryField(
        precision=Aoi.PRECISION, remove_duplicates=True
    )

    def to_representation(self, instance):
        """
        Output a single AOI as a FeatureCollection, even though there is only one Feature
        """
        representation = super().to_representation(instance)
        return OrderedDict((
            ("type", "FeatureCollection"),
            ("features", [representation]),
        ))

    def to_internal_value(self, data):
        """
        Extracts the single feature from the FeatureCollection
        """

        feature = data["features"][0]
        return super().to_internal_value(feature)
