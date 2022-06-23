from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SocialConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'safers.social'
    verbose_name = _("Safers Social")

    def ready(self):

        try:
            # register any checks...
            import safers.social.checks
        except ImportError:
            pass

        try:
            # register any signals...
            import safers.social.signals
        except ImportError:
            pass
