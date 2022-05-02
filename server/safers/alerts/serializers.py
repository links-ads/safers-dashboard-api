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
            "message",
        )

    geometry = AlertGeometrySerializer(many=True, source="geometries")
    message = serializers.JSONField(write_only=True)

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