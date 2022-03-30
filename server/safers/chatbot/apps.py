from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ChatbotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'safers.chatbot'
    verbose_name = _("Safers Chatbot")

    def ready(self):

        try:
            # register any checks...
            import safers.chatbot.checks
        except ImportError:
            pass

        try:
            # register any signals...
            import safers.chatbot.signals
        except ImportError:
            pass
