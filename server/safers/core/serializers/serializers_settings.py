from rest_framework import serializers

from safers.core.models import SafersSettings


class SafersSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SafersSettings
        fields = (
            "allow_local_signin",
            "allow_remote_signin",
            "allow_signup",
            "require_verification",
            "require_terms_acceptance",
            "polling_frequency",
            "request_timeout",
            "max_favorite_alerts",
            "max_favorite_events",
        )
