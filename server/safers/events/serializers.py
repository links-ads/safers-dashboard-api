from django.utils import timezone

from rest_framework import serializers
from rest_framework_gis import serializers as gis_serializers

from drf_spectacular.utils import extend_schema_field

from safers.events.models import Event, EventStatusChoices


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = (
            "id",
            "title",
            "description",
            "start_date",
            "end_date",
            "people_affected",
            "causalties",
            "estimated_damage",
            "alerts",
            "status",
            "geometry",
            "bounding_box",
            "center",
            "alerts",
            "favorite",
        )

    title = serializers.CharField(source="name")

    geometry = serializers.SerializerMethodField()
    center = serializers.SerializerMethodField()
    bounding_box = serializers.SerializerMethodField()

    status = serializers.SerializerMethodField()

    alerts = serializers.SerializerMethodField()

    favorite = serializers.SerializerMethodField(method_name="is_favorite")

    def validate(self, data):
        validated_data = super().validate(data)

        end_date = validated_data.get("end_date")
        if end_date and end_date > timezone.now():
            raise serializers.ValidationError(
                "end_date must not be in the future"
            )

        return validated_data

    @extend_schema_field({
        "type": "object",
        "example": {
            "type":
                "GeometryCollection",
            "geometries": [{
                "type": "Polygon",
                "coordinates": [[
                    [12.97, 77.59],
                    [13.00, 78.00],
                ]]
            }]
        },
    })
    def get_geometry(self, obj) -> dict:
        geometry_serializer = gis_serializers.GeometryField(
            # context=self.context
        )
        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": feature
                }
                for feature in map(
                    lambda x: geometry_serializer.to_representation(x),
                    obj.geometry_collection,
                )
            ]
        }  # yapf: disable

    @extend_schema_field({"type": "object", "example": [12.9721, 77.5933]})
    def get_center(self, obj):
        coords = obj.center.coords
        return map(lambda x: round(x, Event.PRECISION), coords)

    @extend_schema_field({
        "type": "object", "example": [12.97, 77.59, 13.00, 78.00]
    })
    def get_bounding_box(self, obj) -> list:
        coords = obj.bounding_box.extent
        return map(lambda x: round(x, Event.PRECISION), coords)

    def get_status(self, obj) -> str:
        if obj.closed:
            return EventStatusChoices.CLOSED
        elif obj.ongoing:
            return EventStatusChoices.ONGOING

    @extend_schema_field({
        "type": "object", "example": [{
            "id": "uuid", "title": "string"
        }]
    })
    def get_alerts(self, obj) -> list:
        """
        returns some high-level details of the alerts comprising this event
        """
        return [{
            "id": alert.id,
            "title": alert.title,
        } for alert in obj.alerts.only("id", "category")]

    def is_favorite(self, obj) -> bool:
        user = self.context["request"].user
        return obj in user.favorite_events.all()
