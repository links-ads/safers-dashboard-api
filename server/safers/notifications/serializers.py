from rest_framework import serializers
from rest_framework_gis import serializers as gis_serializers

from safers.notifications.models import Notification, NotificationGeometry


class NotificationGeometrySerializer(gis_serializers.GeoFeatureModelSerializer):
    class Meta:
        model = NotificationGeometry
        fields = (
            "description",
            "geometry",
        )
        geo_field = "geometry"
        id_field = False


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = (
            "id",
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

    geometry = NotificationGeometrySerializer(many=True, source="geometries")
    message = serializers.JSONField(write_only=True)

    def create(self, validated_data):
        geometries_data = validated_data.pop("geometries", {})
        notification = super().create(validated_data)
        for geometry_data in geometries_data:
            notification_geometry = NotificationGeometry(
                **geometry_data, notification=notification
            )
            notification_geometry.save()
        return notification
