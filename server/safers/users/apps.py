from django.apps import AppConfig


class UserConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'safers.users'

    try:
        # register any checks...
        import safers.users.checks  
    except ImportError:
        pass

    try:
        # register any signals...
        import safers.users.signals  
    except ImportError:
        pass

