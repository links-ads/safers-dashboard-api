from django.conf import settings

MESSAGE_USER_ID = settings.CELERY_USERNAME
MESSAGE_DELIVERY_MODE = "persistent"