from collections import defaultdict

from django.conf import settings

from rest_framework import serializers
from rest_framework.utils.serializer_helpers import ReturnDict

from drf_yasg.utils import swagger_serializer_method

from safers.aois.models import Aoi

from safers.alerts.models import Alert

from safers.events.models import Event

from safers.cameras.models import CameraMedia

from safers.users.models import User, Organization, Role
from safers.users.serializers import UserProfileSerializer


class UserSerializerLite(serializers.ModelSerializer):
    """
    A "lite" serializer just for some high-level user details
    (can be used by LoginView & RegisterView)
    """
    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "accepted_terms",
            "is_verified",
            "last_login",
            "is_local",
            "is_remote",
        )

    last_login = serializers.DateTimeField(read_only=True)

    @swagger_serializer_method(serializer_or_field=serializers.BooleanField)
    def is_verified(self, obj):
        return obj.is_verified


class UserSerializer(UserSerializerLite):
    """
    The "real" User Serializer; used for CRUD operations
    """
    class Meta:
        model = User
        fields = UserSerializerLite.Meta.fields + (
            "organization",
            "role",
            "default_aoi",
            "profile",
        )

    organization = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.active(), required=False, allow_null=True
    )

    role = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.active(), required=False, allow_null=True
    )

    default_aoi = serializers.PrimaryKeyRelatedField(
        queryset=Aoi.objects.active(), required=False, allow_null=True
    )

    profile = UserProfileSerializer()

    @property
    def errors(self):
        errors = defaultdict(list, super().errors)
        for k, v in errors.pop("profile", {}).items():
            errors[k].append(*v)
        return errors

    def validate(self, data):
        validated_data = super().validate(data)

        if (validated_data["organization"] is not None
           ) and (validated_data["role"].name.lower() == "citizen"):
            raise serializers.ValidationError(
                "A citizen must not belong to an organization."
            )
        return validated_data

    def validate_username(self, value):
        if value in settings.ACCOUNT_USERNAME_BLACKLIST:
            raise serializers.ValidationError(
                f"{value} is not an allowed username"
            )
        return value

    def to_representation(self, instance):
        """
        moves serialized profile data up to root level
        """
        representation = super().to_representation(instance)
        representation.update(representation.pop("profile"))
        return representation

    def to_internal_value(self, data):
        """
        moves root level profile fields back into nested object
        """
        data["profile"] = {
            k: data.get(k)
            for k in UserProfileSerializer.Meta.fields if k in data
        }
        return super().to_internal_value(data)

    def update(self, instance, validated_data):
        profile_serializer = UserProfileSerializer(
            instance.profile, context=self.context
        )
        profile_serializer.update(
            instance.profile, validated_data.pop("profile", {})
        )
        return super().update(instance, validated_data)

    # # no need to override create (safers doesn't create users via DRF)
    # def create(self, validated_data):
    #     profile_serializer = UserProfileSerializer(context=self.context)
    #     profile_data = validated_data.pop("profile", {})
    #     profile = profile_serializer.create(profile_data)
    #     user = User.objects.create(profile=profile, **validated_data)
    #     return user
