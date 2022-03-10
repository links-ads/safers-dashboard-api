from django.contrib.sites.shortcuts import get_current_site

from allauth.account import app_settings as allauth_settings
from allauth.account.adapter import get_adapter
from allauth.account.forms import default_token_generator
from allauth.account.utils import user_username

from dj_rest_auth.forms import AllAuthPasswordResetForm as DjRestAuthPasswordResetForm


class PasswordResetForm(DjRestAuthPasswordResetForm):
    """
    dj-rest-auth is pretty inconsistent when it comes to forms vs. serializers
    in this case dj-rest-auth overloads the django-allauth PasswordResetForm to customize
    how emails are sent (but it uses serializers / adapters for everything else); I am forced
    to overload this form so that I can use my custom get_password_reset_url fn.
    """
    def save(self, request, **kwargs):
        current_site = get_current_site(request)
        email = self.cleaned_data['email']
        token_generator = kwargs.get('token_generator', default_token_generator)

        for user in self.users:

            adapter = get_adapter(request)

            url = adapter.get_password_reset_url(
                request, user, token_generator=token_generator
            )

            context = {
                'current_site': current_site,
                'user': user,
                'password_reset_url': url,
                'request': request,
            }
            if allauth_settings.AUTHENTICATION_METHOD != allauth_settings.AuthenticationMethod.EMAIL:
                context['username'] = user_username(user)

            adapter.send_mail(
                'account/email/password_reset_key', email, context
            )

        return self.cleaned_data['email']