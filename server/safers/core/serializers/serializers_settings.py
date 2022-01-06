from rest_framework import serializers

from safers.core.models import SafersSettings


class SafersSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SafersSettings
        fields = (
            "allow_registration",
        )
