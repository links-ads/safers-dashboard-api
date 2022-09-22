from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password as django_validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework import serializers

from safers.users.models import Role, Organization


class AuthenticateSerializer(serializers.Serializer):
    """
    serializer used to authenticate code
    """
    code = serializers.CharField(required=False)
    locale = serializers.CharField(required=False)
    userState = serializers.CharField(required=False)
    error = serializers.CharField(required=False)

    def validate(self, data):
        validated_data = super().validate(data)
        if validated_data.get("error") or not validated_data.get("code"):
            raise serializers.ValidationError("bad code")
        return validated_data


class RegisterViewSerializer(serializers.Serializer):

    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    password = serializers.CharField(style={"input_type": "password"})
    role = serializers.SlugRelatedField(
        slug_field="name",
        queryset=Role.objects.active(),
        required=True,
    )
    organization = serializers.SlugRelatedField(
        slug_field="name",
        queryset=Organization.objects.active(),
        required=False,
        allow_null=True,
    )
    accepted_terms = serializers.BooleanField()

    def validate(self, data):
        validated_data = super().validate(data)

        if (validated_data["organization"]
            is not None) and (validated_data["role"].name == "citizen"):
            raise serializers.ValidationError(
                "A citizen must not belong to an organization."
            )
        return validated_data

    def validate_email(self, value):
        if get_user_model().objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "User with this email aready exists"
            )
        return value

    def validate_password(self, value):
        try:
            django_validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value

    def validate_accepted_terms(self, value):
        if value is not True:
            raise serializers.ValidationError("Terms must be accepted")
        return value
