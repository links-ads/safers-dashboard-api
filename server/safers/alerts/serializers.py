from rest_framework import serializers
from rest_framework_gis import serializers as gis_serializers

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
            "media",
            "message",
            "information",
        )

    geometry = AlertGeometrySerializer(
        many=True, source="geometries", required=False
    )
    center = serializers.SerializerMethodField()
    bounding_box = serializers.SerializerMethodField()
    message = serializers.JSONField(write_only=True)

    def get_center(self, obj):
        coords = obj.center.coords
        return map(lambda x: round(x, Alert.PRECISION), coords)

    def get_bounding_box(self, obj):
        coords = obj.bounding_box.extent
        return map(lambda x: round(x, Alert.PRECISION), coords)

    def create(self, validated_data):
        geometries_data = validated_data.pop("geometries", {})
        alert = super().create(validated_data)
        for geometry_data in geometries_data:
            alert_geometry = AlertGeometry(**geometry_data, alert=alert)
            alert_geometry.save()
        return alert

    def update(self, instance, validated_data):

        if instance.type == AlertType.UNVALIDATED and validated_data.get(
            "type"
        ) == AlertType.VALIDATED:
            instance.validate()
        elif instance.type == AlertType.VALIDATED and validated_data.get(
            "type"
        ) == AlertType.UNVALIDATED:
            instance.unvalidate()
        alert = super().update(instance, validated_data)
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
            "media",
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

    def is_favorite(self, obj):
        user = self.context["request"].user
        return obj in user.favorite_alerts.all()