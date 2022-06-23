from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DataConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'safers.data'
    verbose_name = _("Safers Data Products")

    def ready(self):

        try:
            # register any checks...
            import safers.data.checks
        except ImportError:
            pass

        try:
            # register any signals...
            import safers.data.signals
        except ImportError:
            pass
