from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.settings import api_settings as drf_settings

from knox.models import AuthToken as KnoxToken
from knox.settings import knox_settings

from allauth.utils import email_address_exists
from allauth.account import app_settings as allauth_settings
from allauth.account.adapter import get_adapter
from allauth.account.utils import setup_user_email

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

from drf_yasg.utils import swagger_serializer_method

from safers.core.models import SafersSettings
from safers.users.forms import PasswordResetForm
from safers.users.models import Role, Organization
from safers.users.serializers import UserSerializerLite

##############################
# authentication serializers #
##############################


class KnoxTokenSerializer(serializers.Serializer):

    token = serializers.SerializerMethodField()
    expiry = serializers.DateTimeField(
        required=False, format=knox_settings.EXPIRY_DATETIME_FORMAT
    )
    user = knox_settings.USER_SERIALIZER()

    @swagger_serializer_method(serializers.CharField)
    def get_token(self, obj):
        if isinstance(obj, dict):
            # when called from auth/login obj will be a dict instead of a token
            obj = obj["token"]
        return obj.digest


#######################################
# redefined drf-rest-auth serializers #
#######################################


class JWTSerializer(DjRestAuthJWTSerializer):
    """
    Don't include user details when requesting a token
    """
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()
    user = serializers.SerializerMethodField()

    @swagger_serializer_method(serializer_or_field=UserSerializerLite)
    def get_user(self, obj):

        user_serializer = UserSerializerLite(obj['user'], context=self.context)
        return user_serializer.data


class LoginSerializer(DjRestAutLoginSerializer):
    username = serializers.CharField(
        required=False, allow_blank=True
    )  # not used by safers, but still needed by django
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(style={'input_type': 'password'})
    accepted_terms = serializers.BooleanField(required=False)

    # TODO: WHILE EMAIL ISN'T WORKING, EVEN IF ALLAUTH IS SET FOR MANDATORY VERIFICATION
    # TODO: DON'T BOTHER CHECKING IT IF SafersSettings.require_verification IS FALSE
    @staticmethod
    def validate_email_verification_status(user):
        safers_settings = SafersSettings.load()
        if safers_settings.require_verification:
            DjRestAutLoginSerializer.validate_email_verification_status(user)

    def validate(self, data):
        validated_data = super().validate(data)
        user = validated_data["user"]

        # handle any additional fields added to this serializer...
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


class RegisterSerializer(serializers.Serializer):
    # this works slightly differently than DjRestAuthRegisterSerializer
    # so I am just writing my own class rather than using inheritance
    email = serializers.EmailField(required=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    password = serializers.CharField(
        write_only=True, style={"input_type": "password"}
    )
    role = serializers.SlugRelatedField(
        slug_field="name", queryset=Role.objects.all()
    )
    organization = serializers.SlugRelatedField(
        slug_field="name", queryset=Organization.objects.all()
    )
    accepted_terms = serializers.BooleanField()

    def validate_email(self, email):
        email = get_adapter().clean_email(email)
        if allauth_settings.UNIQUE_EMAIL:
            if email and email_address_exists(email):
                raise serializers.ValidationError(
                    _('A user is already registered with this e-mail address.'),
                )
        return email

    def validate_accepted_terms(self, value):
        safers_settings = SafersSettings.load()
        if safers_settings.require_terms_acceptance and not value:
            raise serializers.ValidationError(
                "Accepting terms & conditions is required."
            )
        return value

    def custom_signup(self, request, user):
        """
        add all the extra fields that are not part of standard dj-rest-auth registration
        """
        user.accepted_terms = self.validated_data.get("accepted_terms")
        user.role = self.validated_data.get("role")
        user.organization = self.validated_data.get("organization")
        user.save()

    @property
    def cleaned_data(self):
        # here is the "pretend form data" I pass to django-allauth
        return {
            "email": self.validated_data.get("email", ""),
            "username": None,
            "first_name": self.validated_data.get("first_name", ""),
            "last_name": self.validated_data.get("last_name", ""),
            "password1": self.validated_data.get("password", ""),
        }

    def save(self, request):
        adapter = get_adapter()
        user = adapter.new_user(request)
        # note the 3rd argument to `save_user` below; we are pretending that
        # this serializer is a form (hence the `cleaned_data` property above)
        user = adapter.save_user(request, user, self, commit=False)
        try:
            adapter.clean_password(self.validated_data["password"], user=user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(
                detail=serializers.as_serializer_error(exc)
            )
        user.save()
        self.custom_signup(request, user)
        setup_user_email(request, user, [])
        return user


class TokenObtainPairSerializer(SimpleJWTTokenObjtainPairSerializer):
    pass
