from .base import *
from .base import env

DEBUG = env("DJANGO_DEBUG", default="true") == "true"

SECRET_KEY = env("DJANGO_SECRET_KEY")

CORS_ORIGIN_ALLOW_ALL = True

#########
# email #
#########

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

########################
# static & media files #
########################

STATICFILES_STORAGE = "safers.core.storage.LocalStaticStorage"
DEFAULT_FILE_STORAGE = "safers.core.storage.LocalMediaStorage"

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "_static"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "_media"

# These next env vars aren't used in development, but they still ought
# to be defined so that the classes in "storages.py" module can load...

STATIC_LOCATION = ""
STATIC_DEFAULT_ACL = ""
PUBLIC_MEDIA_LOCATION = ""
PUBLIC_MEDIA_DEFAULT_ACL = ""
PRIVATE_MEDIA_LOCATION = ""
PRIVATE_MEDIA_DEFAULT_ACL = ""

###########
# logging #
###########

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s]: %(message)s"
        }
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG",
    },
}

#############
# profiling #
#############

MIDDLEWARE += [
    "silk.middleware.SilkyMiddleware",
    "django_cprofile_middleware.middleware.ProfilerMiddleware",
]

DJANGO_CPROFILE_MIDDLEWARE_REQUIRE_STAFF = False
