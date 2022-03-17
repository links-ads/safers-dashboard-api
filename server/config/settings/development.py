from .base import *
from .base import env

DEBUG = env("DJANGO_DEBUG", default="true") == "true"

SECRET_KEY = env("DJANGO_SECRET_KEY")

CORS_ORIGIN_ALLOW_ALL = True

#########
# email #
#########

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

###############
# Media files #
###############

MEDIA_URL = "/media/"
MEDIA_ROOT = str(BASE_DIR / "media")