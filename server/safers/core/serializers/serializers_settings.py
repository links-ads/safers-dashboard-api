from rest_framework import serializers

from drf_spectacular.utils import extend_schema_field

from safers.auth.clients import AUTH_CLIENT

from safers.core.models import SafersSettings


class SafersSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SafersSettings
        fields = (
            "allow_signup",
            "allow_signin",
            "allow_password_change",
            "require_terms_acceptance",
            "allow_remote_deletion",
            "polling_frequency",
            "request_timeout",
            "max_favorite_alerts",
            "max_favorite_events",
            "auth_settings",
        )

    auth_settings = serializers.SerializerMethodField()

    @extend_schema_field({
        "type": "object",
        "example": {
            "refresh_token_expiration_policy": "Fixed",
            "refresh_token_usage_policy": "Reusable",
            "refresh_token_time_to_live": 43200,
            "access_token_time_to_live": 3600,
        }
    })
    def get_auth_settings(self, obj):
        return AUTH_CLIENT.settings
