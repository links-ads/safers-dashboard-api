from .base import *
from .base import env

DEBUG = True

SECRET_KEY = env("DJANGO_SECRET_KEY")

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


###############
# Media files #
###############

MEDIA_URL = "/media/"
MEDIA_ROOT = str(APP_DIR / "media")