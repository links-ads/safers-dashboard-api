from django.conf import settings

from rest_framework import serializers

from drf_yasg.utils import swagger_serializer_method

from safers.aois.models import Aoi

from safers.alerts.models import Alert

from safers.events.models import Event

from safers.users.models import User


class UserSerializerLite(serializers.ModelSerializer):
    """
    A "lite" serializer just for some high-level user details
    (used by LoginView & RegisterView)
    """
    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "accepted_terms",
            "is_verified",
            "accepted_terms",
            "last_login",
        )

    @swagger_serializer_method(serializer_or_field=serializers.BooleanField)
    def is_verified(self, obj):
        return obj.is_verified


class UserSerializer(UserSerializerLite):
    """
    The "real" User Serializer; used for CRUD operations
    """
    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "accepted_terms",
            "is_verified",
            "accepted_terms",
            "last_login",
            "default_aoi",
            "favorite_alerts",
            "favorite_events",
        )

    default_aoi = serializers.PrimaryKeyRelatedField(
        queryset=Aoi.objects.active()
    )

    favorite_alerts = serializers.PrimaryKeyRelatedField(
        queryset=Alert.objects.all(), many=True
    )

    favorite_events = serializers.PrimaryKeyRelatedField(
        queryset=Event.objects.all(), many=True
    )

    def validate_username(self, value):
        if value in settings.ACCOUNT_USERNAME_BLACKLIST:
            raise serializers.ValidationError(
                f"{value} is not an allowed username"
            )
        return value

    # TODO: NESTED SERIALIZERS