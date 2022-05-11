from django.utils import timezone

from rest_framework import serializers
from rest_framework_gis import serializers as gis_serializers

from safers.alerts.models import Alert

from safers.events.models import Event, EventStatus


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = (
            "id",
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
            "favorite",
            "alerts",
        )

    geometry = serializers.SerializerMethodField()
    center = serializers.SerializerMethodField()
    bounding_box = serializers.SerializerMethodField()

    status = serializers.SerializerMethodField()

    favorite = serializers.SerializerMethodField(method_name="is_favorite")

    alerts = serializers.SlugRelatedField(
        many=True, slug_field="id", queryset=Alert.objects.all()
    )

    def validate(self, data):
        validated_data = super().validate(data)

        end_date = validated_data.get("end_date")
        if end_date and end_date > timezone.now():
            raise serializers.ValidationError(
                "end_date must not be in the future"
            )

        return validated_data

    def get_geometry(self, obj):
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

    def get_center(self, obj):
        coords = obj.center.coords
        return map(lambda x: round(x, Event.PRECISION), coords)

    def get_bounding_box(self, obj):
        coords = obj.bounding_box.extent
        return map(lambda x: round(x, Event.PRECISION), coords)

    def get_status(self, obj):
        if obj.closed:
            return EventStatus.CLOSED
        elif obj.open:
            return EventStatus.OPEN

    def is_favorite(self, obj):
        user = self.context["request"].user
        return obj in user.favorite_events.all()
