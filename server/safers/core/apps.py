from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

from safers.core.utils import DynamicSetting


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'safers.core'
    verbose_name = _("Safers Core")

    def ready(self):

        try:
            # register any checks...
            import safers.core.checks
        except ImportError:
            pass

        try:
            # register any signals...
            import safers.core.signals
        except ImportError:
            pass

        # allow variables defined in django.conf.settings to be instances of DynamicSetting
        DynamicSetting.configure()
