"""
Django settings for safers-gateway project.
"""

import environ

from datetime import timedelta
from pathlib import Path

from django.utils.html import escape
from django.utils.text import slugify

import dj_database_url

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
    'django_celery_beat',
    'django_celery_results',
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
    'safers.aois',
  # 'safers.tasks',
  # 'safers.alerts',
  # 'safers.events',
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
    ]
}

REST_KNOX = {
    'SECURE_HASH_ALGORITHM': 'cryptography.hazmat.primitives.hashes.SHA512',
    'AUTH_TOKEN_CHARACTER_LENGTH': 64,
    'TOKEN_TTL': timedelta(hours=10),
    'USER_SERIALIZER': 'safers.users.serializers.UserSerializer',
    'TOKEN_LIMIT_PER_USER': None,
    'AUTO_REFRESH': False,
}

REST_AUTH_TOKEN_MODEL = 'knox.models.AuthToken'
REST_AUTH_TOKEN_CREATOR = 'safers.users.utils.create_knox_token'

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


SWAGGER_SETTINGS = {
    "SECURITY_DEFINITIONS": {
        "Token": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": escape("Enter 'Bearer <token>'"),
        },
        # "Basic": {
        #     "type": "basic"
        # },
    },
    # "USE_SESSION_AUTH": False,
    "DEFAULT_MODEL_RENDERING": "example",
    "DOC_EXPANSION": "none",
    "OPERATIONS_SORTER": None,
    "TAGS_SORTER": "alpha",
}   # yapf: disable

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
ACCOUNT_EMAIL_VERIFICATION = "mandatory"  # "optional" | "none"
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = False
ACCOUNT_USERNAME_BLACKLIST = ["admin", "current", "sentinel"]

ACCOUNT_CONFIRM_EMAIL_CLIENT_URL = env(
    "ACCOUNT_CONFIRM_EMAIL_CLIENT_URL", default=""
)
ACCOUNT_CONFIRM_PASSWORD_CLIENT_URL = env(
    "ACCOUNT_CONFIRM_PASSWORD_CLIENT_URL", default=""
)

FUSION_AUTH_CLIENT_ID = env("FUSION_AUTH_CLIENT_ID", default="")
FUSION_AUTH_CLIENT_SECRET = env("FUSION_AUTH_CLIENT_SECRET", default="")
FUSION_AUTH_API_KEY = env("FUSION_AUTH_API_KEY", default="")
FUSION_AUTH_EXTERNAL_BASE_URL = env("FUSION_AUTH_EXTERNAL_BASE_URL", default="")
FUSION_AUTH_INTERNAL_BASE_URL = env("FUSION_AUTH_INTERNAL_BASE_URL", default="")

# SOCIAL_AUTH_JSONFIELD_ENABLED = True

# SOCIAL_AUTH_FUSIONAUTH_KEY = env("FUSION_AUTH_API_KEY", default="")
# SOCIAL_AUTH_FUSIONAUTH_SECRET = env("FUSION_AUTH_CLIENT_SECRET", default="")