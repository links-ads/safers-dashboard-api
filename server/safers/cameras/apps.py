from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CameraConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'safers.cameras'
    verbose_name = _("Safers Cameras")

    def ready(self):

        try:
            # register any checks...
            import safers.cameras.checks
        except ImportError:
            pass

        try:
            # register any signals...
            import safers.cameras.signals
        except ImportError:
            pass
