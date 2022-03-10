from django.conf import settings

from rest_framework import serializers

from drf_yasg.utils import swagger_serializer_method

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
        )

    def validate_username(self, value):
        if value in settings.ACCOUNT_USERNAME_BLACKLIST:
            raise serializers.ValidationError(
                f"{value} is not an allowed username"
            )
        return value
