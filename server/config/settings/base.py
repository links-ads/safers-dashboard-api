"""
Django settings for safers-dashboard-api project.
"""
import environ
from datetime import timedelta
from functools import partial
from pathlib import Path

from django.utils.html import escape
from django.utils.text import slugify

import dj_database_url

from safers.core.utils import DynamicSetting
from safers.core.utils import backup_filename_template

#########
# Setup #
#########

env = environ.Env()

BASE_DIR = Path(__file__).resolve(strict=True).parents[2]  # (server dir)
CONFIG_DIR = BASE_DIR / "config"
APP_DIR = BASE_DIR / "safers"

PROJECT_NAME = "Safers Dashboard API"
PROJECT_SLUG = slugify(PROJECT_NAME)
PROJECT_EMAIL = "{role}@" + env("DJANGO_EMAIL_DOMAIN", default="astrosat.net")

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

ROOT_URLCONF = "config.urls"

SITE_ID = 1

APPEND_SLASH = True

DEBUG = False  # redefined in environment module
SECRET_KEY = "shhh..."  # redefined in environment module
SECRET_KEY_FALLBACKS = []

########
# Apps #
########

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.sites",
    "django.contrib.staticfiles",
    "django.contrib.gis",
]

THIRD_PARTY_APPS = [
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "anymail",
    "corsheaders",
    "dbbackup",
    "dj_rest_auth",
    "dj_rest_auth.registration",
    "django_filters",
    "drf_yasg",
    "knox",
    "rest_framework",
    "rest_framework_gis",
    "sequences",
    "silk",
    "storages",
]

LOCAL_APPS = [
    "safers.core",
    "safers.users",
    "safers.rmq",
    "safers.aois",
    "safers.alerts",
    "safers.events",
    "safers.cameras",
    "safers.social",
    "safers.chatbot",
    "safers.data",
    "safers.notifications",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

#############
# Databases #
#############

DATABASES = {
    # (see the note in "./_init_.py" about django_on_heroku not recognising postgis)
    "default": dj_database_url.config(conn_max_age=0)
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

DATA_UPLOAD_MAX_NUMBER_FIELDS = 10240

##############
# Migrations #
##############

MIGRATION_MODULES = {
    # (overrides for app migrations go here)
}

############
# Fixtures #
############

FIXTURE_DIRS = [
    # dirs to search in addtion to fixtures directroy of each app
    # (note that data migrations are preferred to fixtures)
]

########################
# static & media files #
########################

# static & media settings are configured in environment module

###########
# Locales #
###########

# TODO: REVIEW https://docs.djangoproject.com/en/4.1/topics/i18n/timezones/#time-zones
# TODO: ALL TIMESTAMPS IN THE BACKEND SHOULD BE UTC

USE_TZ = False  # ?!?
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
LANGUAGE_CODE = "en-gb"

###########
# Caching #
###########

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "cache",  # name of db table
    },
}

#########
# Admin #
#########

ADMIN_URL = "admin/"

ADMIN_SITE_HEADER = f"{PROJECT_NAME} administration console"
ADMIN_SITE_TITLE = f"{PROJECT_NAME} administration console"
ADMIN_INDEX_TITLE = f"Welcome to the {PROJECT_NAME} administration console"

ADMINS = [(PROJECT_NAME, PROJECT_EMAIL.format(role="techdev"))]
MANAGERS = ADMINS

#############
# Templates #
#############

# any templates placed in "safers/core/templates" can override app-specific templates

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [APP_DIR / "core/templates", ],
        # "APP_DIRS": True,  # not needed simce "app_directories.Loader" is specified below
        "OPTIONS": {
            "debug":
                DEBUG,
            "loaders": [
                "django.template.loaders.filesystem.Loader",  # first look at DIRS
                "django.template.loaders.app_directories.Loader",  # then look in each app
            ],
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
            ],
        },
    },
]

##############
# Middleware #
##############

MIDDLEWARE = [
    "silk.middleware.SilkyMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.common.BrokenLinkEmailsMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

#################
# Authentiation #
#################

LOGIN_URL = "login"
LOGOUT_URL = "logout"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

AUTH_USER_MODEL = "users.User"

AUTHENTICATION_BACKENDS = [
    # TODO: REFACTOR THIS
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

ACCOUNT_ADAPTER = "safers.users.adapters.AccountAdapter"
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = "none"  # "mandatory" | "optional" | "none"
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = False
ACCOUNT_USERNAME_BLACKLIST = ["admin", "current", "sentinel"]

ACCOUNT_CONFIRM_EMAIL_CLIENT_URL = env(
    "ACCOUNT_CONFIRM_EMAIL_CLIENT_URL", default=""
)
ACCOUNT_CONFIRM_PASSWORD_CLIENT_URL = env(
    "ACCOUNT_CONFIRM_PASSWORD_CLIENT_URL", default=""
)

OLD_PASSWORD_FIELD_ENABLED = True

# TODO: RENAME THESE...
FUSION_AUTH_API_KEY = env("FUSION_AUTH_API_KEY", default="")
FUSION_AUTH_APPLICATIIN_KEY = env("FUSION_AUTH_APPLICATION_KEY", default="")
FUSION_AUTH_CLIENT_ID = env("FUSION_AUTH_CLIENT_ID", default="")
FUSION_AUTH_CLIENT_SECRET = env("FUSION_AUTH_CLIENT_SECRET", default="")
FUSION_AUTH_TENANT_ID = env("FUSION_AUTH_TENANT_ID", default="")
FUSION_AUTH_URL = env("FUSION_AUTH_URL", default="")
FUSION_AUTH_EXTERNAL_BASE_URL = env(
    "FUSION_AUTH_EXTERNAL_BASE_URL", default=FUSION_AUTH_URL
)
FUSION_AUTH_INTERNAL_BASE_URL = env(
    "FUSION_AUTH_INTERNAL_BASE_URL", default=FUSION_AUTH_URL
)
FUSION_AUTH_REDIRECT_URL = env("FUSION_AUTH_REDIRECT_URL", default="")

#############
# Passwords #
#############

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME":
            "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {
        "NAME":
            "django.contrib.auth.password_validation.CommonPasswordValidator"
    },
    {
        "NAME": "safers.users.validators.SafersPasswordValidator"
    },
]

PASSWORD_HASHERS = [
    # the 1st item in this list is the default hasher
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]

##################
# Security, etc. #
##################

# TODO: REVIEW THESE...

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"

ALLOWED_HOSTS = ["*"]  # redefined in environment module

CLIENT_HOST = env("CLIENT_HOST", default="")

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOWED_ORIGIN_REGEXES = [rf"^{CLIENT_HOST}$"]
if DEBUG:
    CORS_ALLOWED_ORIGIN_REGEXES += [r"^https?://localhost(:\d+)?$"]

# (only using cors on the API)
CORS_URLS_REGEX = r"^/api/.*$"

#########
# Email #
#########

# futher email settings (like backend) configured in environment module

EMAIL_TIMEOUT = 60

SERVER_EMAIL = PROJECT_EMAIL.format(
    role='noreply'
)  # email (errors) sent to admins & managers
DEFAULT_FROM_EMAIL = f"{PROJECT_NAME} <{PROJECT_EMAIL.format(role='noreply')}>"  # all other email

#######
# API #
#######

# DRF - https://www.django-rest-framework.org/api-guide/settings/

# TODO: UPDATE W/ AUTH
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        # 'rest_framework.authentication.BasicAuthentication',
        # 'rest_framework.authentication.SessionAuthentication',
        # 'rest_framework.authentication.TokenAuthentication',
        'knox.auth.TokenAuthentication',
        # 'rest_framework_simplejwt.authentication.JWTAuthentication',
        # 'dj_rest_auth.jwt_auth.JWTCookieAuthentication',
        # 'oauth2_provider.contrib.rest_framework.OAuth2Authentication',
        # 'drf_social_oauth2.authentication.SocialAuthentication',
    ],
}

FILTERS_DEFAULT_LOOKUP_EXPR = "iexact"

# TODO: REMOVE
REST_KNOX = {
    "SECURE_HASH_ALGORITHM": "cryptography.hazmat.primitives.hashes.SHA512",
    "AUTH_TOKEN_CHARACTER_LENGTH": 64,
    "TOKEN_TTL": timedelta(hours=10),
    "USER_SERIALIZER": "safers.users.serializers.UserSerializer",
    "TOKEN_LIMIT_PER_USER": None,
    "AUTO_REFRESH": False,
    "AUTH_HEADER_PREFIX": "Bearer",
}

# TODO: REMOVE
REST_AUTH = {
    "LOGIN_SERIALIZER":
        "safers.users.serializers.LoginSerializer",
    "TOKEN_SERIALIZER":
        "safers.users.serializers.KnoxTokenSerializer",
    "JWT_SERIALIZER":
        "safers.users.serializers.JWTSerializer",
    "JWT_TOKEN_CLAIMS_SERIALIZER":
        "safers.users.serializers.TokenObtainPairSerializer",
    "USER_DETAILS_SERIALIZER":
        "safers.users.serializers.UserDetailsSerializer",
    "PASSWORD_RESET_SERIALIZER":
        "safers.users.serializers.PasswordResetSerializer",
    "PASSWORD_RESET_CONFIRM_SERIALIZER":
        "safers.users.serializers.PasswordResetConfirmSerializer",
    "PASSWORD_CHANGE_SERIALIZER":
        "safers.users.serializers.PasswordChangeSerializer",
    "REGISTER_SERIALIZER":
        "safers.users.serializers.RegisterSerializer",
    "TOKEN_MODEL":
        "knox.models.AuthToken",
    "TOKEN_CREATOR":
        "safers.users.utils.create_knox_token",
    "OLD_PASSWORD_FIELD_ENABLED":
        True,
}

# TODO: REMOVE
SWAGGER_SETTINGS = {
    "SECURITY_DEFINITIONS": {
        "Token": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": escape("Enter 'Bearer <token>'"),
        },
        "OAuth2": {
            "type": "oauth2",
            "flow": "authorizationCode",
            "authorizationUrl": f"{FUSION_AUTH_EXTERNAL_BASE_URL}/oauth2/authorize",
            "tokenUrl": "/api/oauth2/login",
        },
        # "Basic": {
        #     "type": "basic"
        # },
    },
    "OAUTH2_CONFIG": {
      "clientId": FUSION_AUTH_CLIENT_ID,
      "clientSecret": FUSION_AUTH_CLIENT_SECRET,
      "appName": "safers-dashboard",  # PROJECT_SLUG
    },
    # "USE_SESSION_AUTH": False,
    "DEFAULT_MODEL_RENDERING": "example",
    "DOC_EXPANSION": "none",
    "OPERATIONS_SORTER": None,
    "TAGS_SORTER": "alpha",
}   # yapf: disable

# TODO: DRF-SPECTACULAR

###########
# Logging #
###########

# set in environment module

#############
# Profiling #
#############

# set in environment module

# TODO: MOVE TO ENVIRONMENT MODULES
SILKY_PYTHON_PROFILER = True
SILKY_PYTHON_PROFILER_BINARY = False  # (don't bother W/ .prof files yet)
SILKY_AUTHENTICATION = True
SILKY_AUTHORISATION = True
#SILKY_PERMISSIONS = lambda user: user.is_staff or DEBUG
SILKY_MAX_REQUEST_BODY_SIZE = -1  # accept all requests
# SILKY_MAX_RESPONSE_BODY_SIZE = ?!
SILKY_MAX_RECORDED_REQUESTS = 10**4
SILKY_META = True
SILKY_SENSITIVE_KEYS = {
    'username', 'email', 'client_id', 'client_secret', 'password'
}

###########
# Backups #
###########

DBBACKUP_FILENAME_TEMPLATE = partial(backup_filename_template, PROJECT_SLUG)
DBBACKUP_MEDIA_FILENAME_TEMPLATE = partial(
    backup_filename_template, PROJECT_SLUG
)

# further backups settings are configured in environment module

#######
# RMQ #
#######

RMQ = {
    "default": {
        "TRANSPORT": env("DJANGO_RMQ_TRANSPORT", default="amqp"),
        "HOST": env("DJANGO_RMQ_HOST", default="broker"),
        "PORT": env("DJANGO_RMQ_PORT", default="5672"),
        "VHOST": env("DJANGO_RMQ_VHOST", default=""),
        "QUEUE": env("DJANGO_RMQ_QUEUE", default="qastro"),
        "EXCHANGE": env("DJANGO_RMQ_EXCHANGE", default="safers.b2b"),
        "USERNAME": env("DJANGO_RMQ_USERNAME", default=""),
        "PASSWORD": env("DJANGO_RMQ_PASSWORD", default=""),
        "APP_ID": env("DJANGO_RMQ_APP_ID", default="dsh"),
    }
}

############################
# safers-specific settings #
############################

# TODO: REDUCE THESE

SAFERS_ALLOW_SIGNUP = DynamicSetting(
    "core.SafersSettings.allow_signup",
    True,
)
SAFERS_REQUIRE_VERIFICATION = DynamicSetting(
    "core.SafersSettings.require_verification",
    True,
)
SAFERS_REQUIRE_TERMS_ACCEPTANCE = DynamicSetting(
    "core.SafersSettings.require_terms_acceptance",
    True,
)

SAFERS_RESTRICT_DATA_TO_AOI = DynamicSetting(
    "core.SafersSettings.restrict_data_to_aoi",
    False,
)

SAFERS_DEFAULT_TIMERANGE = DynamicSetting(
    "core.SafersSettings.default_timerange",
    timedelta(days=3),
)

SAFERS_CAMERA_MEDIA_TRIGGER_ALERT_TIMERANGE = DynamicSetting(
    "core.SafersSettings.camera_media_trigger_alert_timerange",
    timedelta(hours=6),
)

SAFERS_CAMERA_MEDIA_PRESERVE_TIMERANGE = DynamicSetting(
    "core.SafersSettings.camera_media_preserve_timerange",
    timedelta(days=1),
)
SAFERS_POSSIBLE_EVENT_DISTANCE = DynamicSetting(
    "core.SafersSettings.possible_event_distance",
    10,
)
SAFERS_POSSIBLE_EVENT_TIMERANGE = DynamicSetting(
    "core.SafersSettings.possible_event_timerange",
    72,
)
SAFERS_MAX_FAVORITE_ALERTS = DynamicSetting(
    "core.SafersSettings.max_favorite_alerts",
    3,
)
SAFERS_MAX_FAVORITE_EVENTS = DynamicSetting(
    "core.SafersSettings.max_favorite_events",
    3,
)
SAFERS_MAX_FAVORITE_CAMERA_MEDIA = DynamicSetting(
    "core.SafersSettings.max_favorite_camera_media",
    3,
)

SAFERS_GATEWAY_API_URL = env(
    "SAFERS_GATEWAY_API_URL",
    default="https://api-test.safers-project.cloud/",
)

SAFERS_GEOSERVER_API_URL = env(
    "SAFERS_GEOSERVER_API_URL",
    default="https://geoserver-test.safers-project.cloud/",
)

SAFERS_GEOSERVER_API_URLS = env(
    "SAFERS_GEOSERVER_API_URLS",
    default=
    "https://geoserver-test1.safers-project.cloud/,https://geoserver-test2.safers-project.cloud/,https://geoserver-test3.safers-project.cloud/,https://geoserver-test4.safers-project.cloud/",
).split(",")

SAFERS_GEODATA_API_URL = env(
    "SAFERS_IMPORTER_API_URL",
    default="https://geoapi-test.safers-project.cloud/",
)

SAFERS_DATALAKE_API_URL = env(
    "SAFERS_DATALAKE_API_URL",
    default="https://datalake-test.safers-project.cloud",
)
