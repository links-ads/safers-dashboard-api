"""
Django settings for safers-gateway project.
"""

import environ

from datetime import timedelta
from pathlib import Path

from django.utils.html import escape
from django.utils.text import slugify

import dj_database_url

from safers.core.utils import DynamicSetting

#########
# setup #
#########

env = environ.Env()

BASE_DIR = Path(__file__).resolve(strict=True).parent.parent.parent
CONFIG_DIR = BASE_DIR / "config"
APP_DIR = BASE_DIR / "safers"

PROJECT_NAME = "Safers Gateway"
PROJECT_SLUG = slugify(PROJECT_NAME)

WSGI_APPLICATION = 'config.wsgi.application'

ROOT_URLCONF = 'config.urls'

# some of these are overridden in development / deployment

DEBUG = True

SECRET_KEY = 'shhh...'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SITE_ID = 1

ALLOWED_HOSTS = []

########
# Apps #
########

DJANGO_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'django.contrib.gis',
    'django.contrib.admin',
]  # yapf: disable

THIRD_PARTY_APPS = [
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'anymail',
    'corsheaders',
    'dj_rest_auth',
    'dj_rest_auth.registration',
    'django_filters',
    'drf_yasg',
    'knox',
    'rest_framework',
    'rest_framework_gis',
# 'oauth2_provider',
# 'social_django',
# 'drf_social_oauth2',
# 'rest_framework_simplejwt',
# 'rest_framework.authtoken',
    'storages',
]  # yapf: disable

LOCAL_APPS = [
    'safers.core',
    'safers.users',
    'safers.rmq',
    'safers.aois',
    'safers.alerts',
    'safers.events',
    'safers.cameras',
    'safers.social',
    'safers.chatbot',
    'safers.data',
]  # yapf: disable

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

##############
# middleware #
##############

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

########
# CORS #
########

CLIENT_HOST = env("CLIENT_HOST", default="")

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOWED_ORIGIN_REGEXES = [rf"^{CLIENT_HOST}$"]

if DEBUG:
    CORS_ALLOWED_ORIGIN_REGEXES += [r"^https?://localhost(:\d+)?$"]

# (only using cors on the API)
CORS_URLS_REGEX = r"^/api/.*$"

#############
# templates #
#############

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [APP_DIR / "core/templates", ],
        'APP_DIRS': True,
        'OPTIONS': {
            "debug":
                DEBUG,
            # "loaders": [
            #     # first look at templates in DIRS...
            #     "django.template.loaders.filesystem.Loader",
            #     # then look in the standard place for each INSTALLED_APP...
            #     "django.template.loaders.app_directories.Loader",
            # ],
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # 'social_django.context_processors.backends',
                # 'social_django.context_processors.login_redirect',
            ],
        },
    },
]

############
# Database #
############

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': CONFIG_DIR / 'db.sqlite3',
    }
}

DATABASES = {
    # (see the note in "./_init_.py" about django_on_heroku not recognising postgis)
    "default": dj_database_url.config(conn_max_age=0)
}

#############
# Passwords #
#############

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME':
            'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME':
            'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8
        },
    },
    {
        'NAME':
            'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'safers.users.validators.SafersPasswordValidator',
    },
]

PASSWORD_HASHERS = [
    # make Argon2 the default password hasher (as per https://docs.djangoproject.com/en/4.0/topics/auth/passwords/#using-argon2-with-django)
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    # 'django.contrib.auth.hashers.ScryptPasswordHasher',
]

# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

########################
# static & media files #
########################

# handled in development / deployment

#########
# Admin #
#########

ADMIN_URL = "admin/"

ADMIN_SITE_HEADER = f"{PROJECT_NAME} administration console"
ADMIN_SITE_TITLE = f"{PROJECT_NAME} administration console"
ADMIN_INDEX_TITLE = f"Welcome to the {PROJECT_NAME} administration console"

#################
# Authentiation #
#################

AUTH_USER_MODEL = "users.User"

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
    # 'drf_social_oauth2.backends.DjangoOAuth2',  # local oauth2
    # 'safers.users.backends.FusionAuthBackend',  # remote oauth2
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

FUSION_AUTH_CLIENT_ID = env("FUSION_AUTH_CLIENT_ID", default="")
FUSION_AUTH_CLIENT_SECRET = env("FUSION_AUTH_CLIENT_SECRET", default="")
FUSION_AUTH_API_KEY = env("FUSION_AUTH_API_KEY", default="")
FUSION_AUTH_EXTERNAL_BASE_URL = env("FUSION_AUTH_EXTERNAL_BASE_URL", default="")
FUSION_AUTH_INTERNAL_BASE_URL = env("FUSION_AUTH_INTERNAL_BASE_URL", default="")

# SOCIAL_AUTH_JSONFIELD_ENABLED = True

# SOCIAL_AUTH_FUSIONAUTH_KEY = env("FUSION_AUTH_API_KEY", default="")
# SOCIAL_AUTH_FUSIONAUTH_SECRET = env("FUSION_AUTH_CLIENT_SECRET", default="")

#######
# API #
#######

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

REST_KNOX = {
    "SECURE_HASH_ALGORITHM": "cryptography.hazmat.primitives.hashes.SHA512",
    "AUTH_TOKEN_CHARACTER_LENGTH": 64,
    "TOKEN_TTL": timedelta(hours=10),
    "USER_SERIALIZER": "safers.users.serializers.UserSerializer",
    "TOKEN_LIMIT_PER_USER": None,
    "AUTO_REFRESH": False,
    "AUTH_HEADER_PREFIX": "Bearer",
}

REST_AUTH_TOKEN_MODEL = "knox.models.AuthToken"
REST_AUTH_TOKEN_CREATOR = "safers.users.utils.create_knox_token"

# REST_USE_JWT = True
# JWT_AUTH_COOKIE = "safers-gateway-auth"
# JWT_AUTH_REFRESH_COOKIE = "safers-gateway-refresh"

# custom serializers...
REST_AUTH_SERIALIZERS = {
    "JWT_SERIALIZER": "safers.users.serializers.JWTSerializer",
    "JWT_TOKEN_CLAIMS_SERIALIZER": "safers.users.serializers.TokenObtainPairSerializer",
    "LOGIN_SERIALIZER": "safers.users.serializers.LoginSerializer",
    "PASSWORD_CHANGE_SERIALIZER": "safers.users.serializers.PasswordChangeSerializer",
    "PASSWORD_RESET_SERIALIZER": "safers.users.serializers.PasswordResetSerializer",
    "PASSWORD_RESET_CONFIRM_SERIALIZER": "safers.users.serializers.PasswordResetConfirmSerializer",
    "TOKEN_SERIALIZER": "safers.users.serializers.KnoxTokenSerializer",
    "USER_DETAILS_SERIALIZER": "safers.users.serializers.UserDetailsSerializer",
}  # yapf: disable

# more custom serializers...
REST_AUTH_REGISTER_SERIALIZERS = {
    "REGISTER_SERIALIZER": "safers.users.serializers.RegisterSerializer"
}  # yapf: disable

FILTERS_DEFAULT_LOOKUP_EXPR = "iexact"

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
      "appName": "safers-gateway",  # PROJECT_SLUG
    },
    # "USE_SESSION_AUTH": False,
    "DEFAULT_MODEL_RENDERING": "example",
    "DOC_EXPANSION": "none",
    "OPERATIONS_SORTER": None,
    "TAGS_SORTER": "alpha",
}   # yapf: disable

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

#########
# Tasks #
#########

# TODO...

DJANGO_CELERY_RESULTS = {"ALLOW_EDITS": True}
DJANGO_CELERY_BEAT = {}

CELERY_ACCEPT_CONTENT = ["json"]
CELERY_RESULT_SERIALIZER = "json"
CELERY_TASK_SERIALIZER = "json"
CELERY_TASK_SOFT_TIME_LIMIT = 60 * 5  # 5 minutes until SoftTimeLimitExceeded
CELERY_TASK_TIME_LIMIT = 60 * 25  # 25 minutes until worker is killed & replace

CELERY_DEFAULT_QUEUE_NAME = env(
    "DJANGO_CELERY_DEFAULT_QUEUE_NAME", default="qastro"
)
CELERY_DEFAULT_EXCHANGE_NAME = env(
    "DJANGO_CELERY_DEFAULT_EXCHANGE_NAME", default="safers.b2b"
)
CELERY_DEFAULT_EXCHANGE_TYPE = env(
    "DJANGO_CELERY_DEFAULT_EXCHANGE_TYPE", default="topic"
)

CELERY_USERNAME = env("DJANGO_CELERY_BROKER_USERNAME", default="")
CELERY_PASSWORD = env("DJANGO_CELERY_BROKER_PASSWORD", default="")

CELERY_BROKER_URL = "{transport}://{username}:{password}@{host}:{port}/{virtual_host}".format(
    transport=env("DJANGO_CELERY_BROKER_TRANSPORT", default="amqp"),
    username=env("DJANGO_CELERY_BROKER_USERNAME", default=""),
    password=env("DJANGO_CELERY_BROKER_PASSWORD", default=""),
    host=env("DJANGO_CELERY_BROKER_HOST", default="localhost"),
    port=env("DJANGO_CELERY_BROKER_PORT", default="5672"),
    virtual_host=env("DJANGO_CELERY_BROKER_VIRTUAL_HOST", default=""),
)

CELERY_RESULT_BACKEND = "django-db"  # django-celery-results
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers.DatabaseScheduler"  # django-celery-beat

############################
# safers-specific settings #
############################

SAFERS_ALLOW_REGISTRATION = DynamicSetting(
    "core.SafersSettings.allow_registration", True
)
SAFERS_REQUIRE_VERIFICATION = DynamicSetting(
    "core.SafersSettings.require_verification", True
)
SAFERS_REQUIRE_TERMS_ACCEPTANCE = DynamicSetting(
    "core.SafersSettings.require_terms_acceptance", True
)
SAFERS_POSSIBLE_EVENT_DISTANCE = DynamicSetting(
    "core.SafersSettings.possible_event_distance", 10
)
SAFERS_POSSIBLE_EVENT_TIMERANGE = DynamicSetting(
    "core.SafersSettings.possible_event_timerange", 72
)
SAFERS_MAX_FAVORITE_ALERTS = DynamicSetting(
    "core.SafersSettings.max_favorite_alerts", 3
)
SAFERS_MAX_FAVORITE_EVENTS = DynamicSetting(
    "core.SafersSettings.max_favorite_events", 3
)
SAFERS_MAX_FAVORITE_CAMERA_MEDIA = DynamicSetting(
    "core.SafersSettings.max_favorite_camera_media", 3
)

SAFERS_GATEWAY_API_URL = env(
    "SAFERS_GATEWAY_API_URL",
    default="https://api-test.safers-project.cloud/",
)

SAFERS_GEOSERVER_API_URL = env(
    "SAFERS_GEOSERVER_API_URL",
    default="https://geoserver-test.safers-project.cloud/",
)

SAFERS_GEODATA_API_URL = env(
    "SAFERS_IMPORTER_API_URL",
    default="https://geoapi-test.safers-project.cloud/",
)

SAFERS_DATALAKE_API_URL = env(
    "SAFERS_DATALAKE_API_URL",
    default="https://datalake-test.safers-project.cloud",
)
