from django.conf import settings

from rest_framework import serializers

from safers.users.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "last_login",
        )

    def validate_username(self, value):
        if value in settings.ACCOUNT_USERNAME_BLACKLIST:
            raise serializers.ValidationError(
                f"{value} is not an allowed username"
            )
        return value
