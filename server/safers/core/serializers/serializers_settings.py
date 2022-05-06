from rest_framework import serializers

from safers.core.models import SafersSettings


class SafersSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SafersSettings
        fields = (
            "allow_registration",
            "require_verification",
            "require_terms_acceptance",
            "polling_frequency",
            "max_favorite_alerts",
            "max_favorite_events",
        )
