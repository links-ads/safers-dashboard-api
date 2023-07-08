"""
Custom settings for "development" environment.
"""
from .base import *

#########
# Setup #
#########

env = environ.Env()

DEBUG = True
SECRET_KEY = env("DJANGO_SECRET_KEY", default="shhh")
SECRET_KEY_FALLBACKS = env("DJANGO_SECRET_KEY_FALLBACKS", default=[])

########
# Apps #
########

INSTALLED_APPS += []

CORS_ORIGIN_ALLOW_ALL = True

########################
# static & media files #
########################

STORAGES = {
    "default": {
        "BACKEND": "safers.core.storage.LocalMediaStorage",
    },
    "staticfiles": {
        "BACKEND": "safers.core.storage.LocalStaticStorage",
    }
}

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

##################
# Security, etc. #
##################

ALLOWED_HOSTS = ["*"]
CORS_ALLOW_ALL_ORIGINS = True

#########
# Email #
#########

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

#######
# API #
#######

# TODO: DRF-SPECTACULAR [SIDECAR]

###########
# Logging #
###########

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {},
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        },
        "colored": {
            "()": "safers.core.logging.ColoredFormatter",
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "filters": [],
            "formatter": "colored",
        },
        "mail_admins": {
            "class": "django.utils.log.AdminEmailHandler",
            "filters": [],
            "level": "ERROR",
        },
    },
    "loggers": {
        # change the level of a few particularly verbose loggers
        "django.db.backends": {
            "level": "WARNING"
        },
        "django.utils.autoreload": {
            "level": "WARNING"
        },
        "faker": {
            "level": "WARNING"
        },
    },
    "root": {
        "handlers": [
            "console",
            # "mail_admins",  # don't bother w/ AdminEmailHandler for DEVELOPMENT
        ],
        "level": "DEBUG",
    },
}

#############
# Profiling #
#############

SILKY_MAX_REQUEST_BODY_SIZE = -1  # accept all requests
# SILKY_MAX_RESPONSE_BODY_SIZE = 1024
SILKY_MAX_RECORDED_REQUESTS = 10**4

SILKY_STORAGE_CLASS = "silk.storage.ProfilerResultStorage"
SILKY_PYTHON_PROFILER_RESULT_PATH = f"{MEDIA_ROOT}/profiling/"

###########
# Backups #
###########

DBBACKUP_STORAGE = "safers.core.storage.LocalMediaStorage"
DBBACKUP_STORAGE_OPTIONS = {"location": f"{MEDIA_ROOT}/backups/"}
