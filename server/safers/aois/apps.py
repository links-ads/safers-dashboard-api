from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AoiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'safers.aois'
    verbose_name = _("Safers AOIs")

    def ready(self):

        try:
            # register any checks...
            import safers.aois.checks
        except ImportError:
            pass

        try:
            # register any signals...
            import safers.aois.signals
        except ImportError:
            pass
