from django.conf import settings
from django.contrib.auth import get_user_model

from rest_framework.exceptions import APIException

from allauth.account import app_settings as allauth_settings
from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.forms import default_token_generator
from allauth.account.utils import (
    user_email,
    user_field,
    user_username,
    user_pk_to_url_str,
    url_str_to_user_pk,
)
# from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

UserModel = get_user_model()


class AccountAdapter(DefaultAccountAdapter):
    """
    custom tweaks to django-allauth
    """
    def is_open_for_signup(self, request):
        return settings.SAFERS_ALLOW_REGISTRATION

    def check_user(self, user, **kwargs):
        """
        Here is where I put all the custom checks that I want to happen
        which aren't necessarily form/serializer errors.
        """

        # verification (overriding the check here in order to not automatically resend the verification email)
        if (
            kwargs.get("check_verification", True) and
            settings.SAFERS_REQUIRE_VERIFICATION and not user.is_verified
        ):
            # send_email_confirmation(request, user)
            raise APIException(f"User {user} is not verified.")

        # terms acceptance
        if (
            kwargs.get("check_terms_acceptance", True) and
            settings.SAFERS_REQUIRE_TERMS_ACCEPTANCE and not user.accepted_terms
        ):
            raise APIException(
                "Please accept our latest Terms & Conditions and Privacy Policy."
            )

        # change_password (redirecting to reset_password_view)
        if kwargs.get("check_password", True) and user.change_password:
            self.send_password_confirmation_email(user, user.email)
            raise APIException("A password reset email has been sent.")

        return True

    def populate_username(self, request, user):
        """
        Fills in a valid username, if required and missing.
        Customizing this to use email as username
        """

        email = user_email(user)
        username = user_username(user)
        if username is None:
            user_field(user, allauth_settings.USER_MODEL_USERNAME_FIELD, email)

    def get_email_confirmation_url(self, request, emailconfirmation):

        url = settings.ACCOUNT_CONFIRM_EMAIL_CLIENT_URL.format(
            key=emailconfirmation.key
        )
        return url

    def get_password_reset_url(
        self, request, user, token_generator=default_token_generator
    ):

        url = settings.ACCOUNT_CONFIRM_PASSWORD_CLIENT_URL.format(
            uid=user_pk_to_url_str(user),
            key=token_generator.make_token(user),
        )
        return url
