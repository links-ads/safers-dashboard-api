from django.conf import settings

from rest_framework import serializers
from rest_framework.settings import api_settings as drf_settings

from allauth.account.adapter import get_adapter

from dj_rest_auth.serializers import (
    JWTSerializer as DjRestAuthJWTSerializer,
    LoginSerializer as DjRestAutLoginSerializer,
    PasswordChangeSerializer as DjRestAuthPasswordChangeSerializer,
    PasswordResetSerializer as DjRestAuthPasswordResetSerializer,
    PasswordResetConfirmSerializer as DjRestAuthPasswordResetConfirmSerializer,
    TokenSerializer as DjRestAuthTokenSerializer,
    UserDetailsSerializer as DjRestAuthUserDetailsSerializer,
)

from dj_rest_auth.registration.serializers import (
    RegisterSerializer as DjRestAuthRegisterSerializer,
)

from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer as SimpleJWTTokenObjtainPairSerializer,
)

from safers.users.forms import PasswordResetForm


class JWTSerializer(DjRestAuthJWTSerializer):
    """
    Don't include user details when requesting a token
    """
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()
    user = None


class LoginSerializer(DjRestAutLoginSerializer):
    username = serializers.CharField(
        required=False, allow_blank=True
    )  # not used by safers, but still needed by django
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(style={'input_type': 'password'})
    accepted_terms = serializers.BooleanField(required=False)

    def validate(self, data):
        validated_data = super().validate(data)
        user = validated_data["user"]

        # the user might have explicitly accepted/unaccepted terms
        accepted_terms = validated_data.get("accepted_terms")
        if accepted_terms is not None:
            user.accepted_terms = accepted_terms
            user.save()

        # at this point I've successfully have the user,
        # but I want to perform additional checks on them...
        try:
            adapter = get_adapter(self.context.get("request"))
            adapter.check_user(user)
        except Exception as e:
            msg = {
                drf_settings.NON_FIELD_ERRORS_KEY: str(e),
            }
            raise serializers.ValidationError(msg)

        return validated_data


class PasswordChangeSerializer(DjRestAuthPasswordChangeSerializer):
    pass


class PasswordResetSerializer(DjRestAuthPasswordResetSerializer):
    @property
    def password_reset_form_class(self):
        # use a custom form to send the actual email
        return PasswordResetForm


class PasswordResetConfirmSerializer(DjRestAuthPasswordResetConfirmSerializer):
    pass


class TokenSerializer(DjRestAuthTokenSerializer):
    pass


class UserDetailsSerializer(DjRestAuthUserDetailsSerializer):
    pass


class RegisterSerializer(DjRestAuthRegisterSerializer):
    pass


class TokenObtainPairSerializer(SimpleJWTTokenObjtainPairSerializer):
    pass
