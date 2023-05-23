"""
All the serializers used for the auth views.  Note that these are _not_
ModelSerializers; They are used for validation of request data only. 
Interacting with the underlying models is not done by DRF but by proxying
the requests to the actual FusionAuth endpoints.
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password as django_validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueValidator

from drf_spectacular.utils import extend_schema_serializer

from safers.core.models import SafersSettings
from safers.core.serializers import ContextVariableDefault

from safers.users.models import Organization, Role

UserModel = get_user_model()


def validate_password(validated_data):
    if "password_confirmation" in validated_data:
        if validated_data["password"] != validated_data["password_confirmation"]:
            raise ValidationError({
                "password_confirmation": "Passwords must match."
            })

    try:
        django_validate_password(
            validated_data["password"],
            user=UserModel(email=validated_data.get("email")),
        )
    except DjangoValidationError as exception:
        raise ValidationError({"password": exception.messages}) from exception


@extend_schema_serializer(
    exclude_fields=["organization", "role"]
)  # TOOD: FIGURE OUT A BETTER WAY TO PREVENT drf-spectacular FROM QUEYRING THESE FIELDS
class RegisterViewSerializer(serializers.Serializer):
    """
    Used to validate all the fields on the registration form.
    """
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=UserModel.objects.all())]
    )

    username = serializers.CharField(
        default=ContextVariableDefault("username", raise_error=True)
    )

    password = serializers.CharField(style={"input_type": "password"})

    first_name = serializers.CharField(required=False, source="firstName")

    last_name = serializers.CharField(required=False, source="lastName")

    organization = serializers.SlugRelatedField(
        slug_field="name",
        queryset=Organization.objects.all(),
        required=False,
        allow_null=True,
    )

    role = serializers.SlugRelatedField(
        slug_field="name",
        queryset=Role.objects.all(),
        required=True,
    )

    accepted_terms = serializers.BooleanField()

    def validate_accepted_terms(self, value):
        safers_settings = SafersSettings.load()
        if safers_settings.require_terms_acceptance and not value:
            raise ValidationError("Terms must be accepted.")
        return value

    def validate(self, data):
        validated_data = super().validate(data)

        # make sure password conforms to the rules specified in AUTH_PASSWORD_VALIDATORS
        validate_password(validated_data)

        # make sure organization & role are compatible
        organization = validated_data.get("organization")
        role = validated_data.get("role")
        if organization and role.is_citizen:
            raise ValidationError(
                "A citizen must not belong to an organization."
            )

        return validated_data


class AuthenticateViewSerializer(serializers.Serializer):
    """
    Used to validate the response from FusionAuth for the authorization_code_grant
    """
    code = serializers.CharField(required=False)
    locale = serializers.CharField(required=False)
    userState = serializers.CharField(required=False)
    error = serializers.CharField(required=False)

    def validate(self, data):
        validated_data = super().validate(data)
        error = validated_data.get("error")
        if error:
            raise ValidationError(error)
        return validated_data


class RefreshViewSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(required=False)