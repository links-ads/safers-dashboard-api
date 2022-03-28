from django.conf import settings

from celery import shared_task

from safers.tasks.celery import app as celery_app


# TODO: PASS ROUTING_KEY AS ARG/KWARG
@shared_task
def publish_message(message):
    with celery_app.producer_pool.acquire(block=True) as producer:
        producer.publish(
            message,
            exchange=settings.CELERY_DEFAULT_EXCHANGE_NAME,
            routing_key='mykey',
        )
