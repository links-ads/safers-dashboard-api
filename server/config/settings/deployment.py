from .base import *
from .base import env

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

DEBUG = env("DJANGO_DEBUG", default="false") == "true"

SECRET_KEY = env("DJANGO_SECRET_KEY")

CORS_ORIGIN_ALLOW_ALL = True

#########
# email #
#########

# TODO: I ACTUALLY WANT TO USE A "PROPER ESP VIA ANYMAIL
# TODO: (LIKE SENDMAIL VIA HEROKU), BUT IT TAKES TIME TO
# TODO: SET UP PROPERLY.  SO FOR NOW I'M USING GMAIL :(
# EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"
# DEFAULT_FROM_EMAIL = "noreply@safers.com"
# SERVER_EMAIL = "noreply@safers.com"
# ANYMAIL = {
#     "MAILGUN_API_KEY":
#         env("MAILGUN_API_KEY", default=""),
#     "MAILGUN_DOMAIN":
#         env("MAILGUN_DOMAIN", default=""),
#     "MAILGUN_PUBLIC_KEY":
#         env("MAILGUN_PUBLIC_KEY", default=""),
#     "MAILGUN_SMTP_LOGIN":
#         env("MAILGUN_SMTP_LOGIN", default=""),
#     "MAILGUN_SMTP_PASSWORD":
#         env("MAILGUN_SMTP_PASSWORD", default=""),
#     "MAILGUN_SMTP_PORT":
#         env("MAILGUN_SMTP_PORT", default=""),
#     "MAILGUN_SMTP_SERVER":
#         env("MAILGUN_SMTP_SERVER", default=""),
#     "MAILGUN_WEBHOOK_SIGNING_KEY":
#         env("MAILGUN_WEBHOOK_SIGNING_KEY", default=""),
#     "MAILGUN_SENDER_DOMAIN":
#         env("MAILGUN_SENDER_DOMAIN", default=""),
# }

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env("EMAIL_HOST_PORT", default=587)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")

DEFAULT_FROM_EMAIL = env("EMAIL_HOST_USER", default=EMAIL_HOST_USER)

#########
# media #
#########

# Using Bucketeer to allow Heroku to manage storage in AWS S3.  PublicMediaS3Storage is
# used by default; I can also specify PrivateMediaS3Storage on a field-by-field basis.

STATICFILES_STORAGE = "safers.core.storage.StaticS3Storage"
DEFAULT_FILE_STORAGE = "safers.core.storage.PublicMediaS3Storage"

AWS_ACCESS_KEY_ID = env("BUCKETEER_AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env("BUCKETEER_AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = env("BUCKETEER_BUCKET_NAME")
AWS_S3_ENDPOINT_URL = f"https://{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"
AWS_S3_REGION_NAME = env("BUCKETEER_AWS_REGION")
AWS_S3_SIGNATURE_VERSION = env("S3_SIGNATURE_VERSION", default="s3v4")
AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400"}
AWS_DEFAULT_ACL = None

STATIC_DEFAULT_ACL = 'public-read'
STATIC_LOCATION = 'static'
STATIC_URL = f'{AWS_S3_ENDPOINT_URL}/{STATIC_LOCATION}/'

PUBLIC_MEDIA_DEFAULT_ACL = 'public-read'
PUBLIC_MEDIA_LOCATION = 'media/public'
PUBLIC_MEDIA_URL = f'{AWS_S3_ENDPOINT_URL}/{PUBLIC_MEDIA_LOCATION}/'

PRIVATE_MEDIA_DEFAULT_ACL = 'private'
PRIVATE_MEDIA_LOCATION = 'media/private'
PRIVATE_MEDIA_URL = f'{AWS_S3_ENDPOINT_URL}/{PRIVATE_MEDIA_LOCATION}/'

###########
# logging #
###########

SENTRY_DSN = env("DJANGO_SENTRY_DSN", default=None)
SENTRY_ENV = env("DJANGO_SENTRY_ENV", default=None)
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=SENTRY_ENV,
        integrations=[
            DjangoIntegration(),
        ],

        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production.
        traces_sample_rate=1.0,

        # If you wish to associate users to errors (assuming you are using
        # django.contrib.auth) you may enable sending PII data.
        send_default_pii=True
    )

###########
# backups #
##########

DBBACKUP_STORAGE = "safers.core.storage.PrivateMediaS3Storage"
DBBACKUP_STORAGE_OPTIONS = {
    "location": "backups",
    "access_key": AWS_ACCESS_KEY_ID,
    "secret_key": AWS_SECRET_ACCESS_KEY,
    "bucket_name": AWS_STORAGE_BUCKET_NAME,
    "default_acl": AWS_DEFAULT_ACL,
}
