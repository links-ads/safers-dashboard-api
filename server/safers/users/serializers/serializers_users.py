from rest_framework import serializers

from safers.users.models import User, Organization, Role


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "auth_id",
            "email",
            "username",
            "status",
            "accepted_terms",
            "change_password",
            "organization_name",
            "role_name",
            "organization",
            "role",
            "profile",
            "is_citizen",
            "is_professional",
            "default_aoi",
        )

    auth_id = serializers.UUIDField(
        required=False,
        write_only=True,
    )

    organization_name = serializers.CharField(
        required=False,
        write_only=True,
    )

    role_name = serializers.CharField(
        required=False,
        write_only=True,
    )

    organization = serializers.SlugRelatedField(
        slug_field="name",
        read_only=True,
    )

    role = serializers.SlugRelatedField(
        slug_field="name",
        read_only=True,
    )