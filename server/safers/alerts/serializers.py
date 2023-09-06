from rest_framework import serializers
from rest_framework_gis import serializers as gis_serializers

from drf_spectacular.utils import extend_schema_field

from safers.alerts.models import Alert, AlertGeometry, AlertType


class AlertGeometrySerializer(gis_serializers.GeoFeatureModelSerializer):
    class Meta:
        model = AlertGeometry
        fields = (
            "description",
            "geometry",
        )
        geo_field = "geometry"
        id_field = False


class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = (
            "id",
            "type",
            "timestamp",
            "status",
            "source",
            "scope",
            "category",
            "event",
            "urgency",
            "severity",
            "certainty",
            "description",
            "geometry",
            "center",
            "bounding_box",
            "message",
            "information",
        )

    geometry = AlertGeometrySerializer(
        many=True, source="geometries", required=False
    )
    center = serializers.SerializerMethodField()
    bounding_box = serializers.SerializerMethodField()
    message = serializers.JSONField(write_only=True)

    @extend_schema_field({"type": "object", "example": [12.9721, 77.5933]})
    def get_center(self, obj):
        coords = obj.center.coords
        return map(lambda x: round(x, Alert.PRECISION), coords)

    @extend_schema_field({
        "type": "object", "example": [12.97, 77.59, 13.00, 78.00]
    })
    def get_bounding_box(self, obj):
        coords = obj.bounding_box.extent
        return map(lambda x: round(x, Alert.PRECISION), coords)

    def validate_type(self, value):
        if self.instance and self.instance.type != value:
            raise serializers.ValidationError(
                "alert.type can only be changed using the 'validate' endpoint."
            )
        return value

    def create(self, validated_data):
        geometries_data = validated_data.pop("geometries", {})
        alert = super().create(validated_data)
        for geometry_data in geometries_data:
            alert_geometry = AlertGeometry(**geometry_data, alert=alert)
            alert_geometry.save()
        return alert


class AlertViewSetSerializer(AlertSerializer):
    """
    The serializer used by the AlertViewSet.  This is different from the default serializer which is used by
    RMQ.  The latter allows all fields to be updated.  The former only allows "information" & "type"
    """
    class Meta:
        model = Alert
        fields = (
            "id",
            "title",
            "type",
            "timestamp",
            "status",
            "source",
            "scope",
            "category",
            "event",
            "urgency",
            "severity",
            "certainty",
            "description",
            "geometry",
            "center",
            "bounding_box",
            "media_urls",
            "information",
            "favorite",
        )
        extra_kwargs = {
            "timestamp": {"read_only": True},
            "status": {"read_only": True},
            "source": {"read_only": True},
            "scope": {"read_only": True},
            "category": {"read_only": True},
            "event": {"read_only": True},
            "urgency": {"read_only": True},
            "severity": {"read_only": True},
            "certainty": {"read_only": True},
            "description": {"read_only": True},
            "geometry": {"read_only": True},
        }  # yapf: disable

    favorite = serializers.SerializerMethodField(method_name="is_favorite")

    def is_favorite(self, obj) -> bool:
        # a bit of indirection here to prevent multiple db hits
        favorite_alert_ids = self.context.get("favorite_alert_ids", [])
        return obj.id in favorite_alert_ids
