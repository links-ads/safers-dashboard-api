from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AuthConfig(AppConfig):
    name = 'safers.auth'
    verbose_name = _("Safers Auth")
    label = "safers_auth"  # unique label so as not to conflict w/ "django.contrib.auth"

    def ready(self):

        try:
            # register any checks...
            import safers.auth.checks
        except ImportError:
            pass

        try:
            # register any signals...
            import safers.auth.signals
        except ImportError:
            pass

        # register any custom swagger extensions
        # (to enable authentication via drf-spectacular)...
        # (as per https://drf-spectacular.readthedocs.io/en/latest/faq.html#where-should-i-put-my-extensions-my-extensions-are-not-detected)
        import safers.auth.schema
