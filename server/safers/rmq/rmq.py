import json
import re
import logging
from importlib import import_module
from dataclasses import dataclass
from datetime import datetime

from django.conf import settings

import pika
from pika.frame import Method
from pika import BasicProperties

import ssl

logger = logging.getLogger(__name__)

#################
# routing table #
#################

BINDING_KEYS = {
    # a map of routing_key patterns to handlers
    "status.test.*": (),
    "event.social.wildfire": ("safers.social.models.SocialEvent", ),
    # "mm.communication.*": ("safers.chatbot.models.Communication",),
    # "mm.mission.*": ("safers.chatbot.models.Mission",),
    # "mm.report.*": ("safers.chatbot.models.Report", ),
    "newexternaldata.*": ("safers.data.models.Data", ),
    "alert.sem.astro": ("safers.alerts.models.Alerts", ),
    "notification.sem.astro": ("safers.notifications.models.Notification", ),
    "event.camera.#": ("safers.cameras.models.CameraMedia", ),
}


def binding_key_to_regex(binding_key):

    # "#" maps to any characters
    # "*" maps to any characters in a single section

    regex = binding_key.replace(".", "\.").replace("*", "[^\.]+").replace("#", ".*")  # yapf: disable
    return "^" + regex + "$"


def import_callable(path_or_callable):
    """
    Takes a callable (class or function) or a path to callable
    and return the appropriate method to process a message with;
    In the case of a function this will be itself, in the case of a
    class this will be the "process_message" method.
    """

    if hasattr(path_or_callable, '__call__'):
        callable = path_or_callable
    else:
        assert isinstance(path_or_callable, str)
        package, attr = path_or_callable.rsplit('.', 1)
        callable = getattr(import_module(package), attr)

    if not isinstance(callable, type):
        return callable
    return getattr(callable, "process_message")


##########
# config #
##########


@dataclass
class RMQConf:
    username: str
    password: str
    host: str
    queue: str = "qastro.test"
    exchange: str = "safers.b2b"
    port: str = "5672"
    vhost: str = None
    transport: str = "amqp"
    app_id: str = "dsh"


#####################
# interface for RMQ #
#####################


class RMQ(object):
    """
    class for communicating w/ RabbitMQ
    (based on https://bitbucket.org/mobilesolutionsismb/rabbit-example-safers/src/master/python/receiver.py)
    """
    def __init__(self):
        # self.config = RMQConf(**settings.RMQ["default"])
        self.config = RMQConf(
            **dict((k.lower(), v) for k, v in settings.RMQ["default"].items())
        )

        # set credentials and SSL params
        credentials = pika.PlainCredentials(
            self.config.username, self.config.password
        )

        # uncomment following line if you encounter troubles with certification authority validation
        # ssl_options = pika.SSLOptions(ssl.create_default_context(cafile=config.CA_FILE),config.RMQ_HOST)
        # comment following line if you encounter troubles with certification authority validation
        ssl_options = pika.SSLOptions(
            ssl.create_default_context(), self.config.host
        )

        # create the connection parameters
        self.params = pika.ConnectionParameters(
            host=self.config.host,
            port=self.config.port,
            virtual_host=self.config.vhost,
            credentials=credentials,
            ssl_options=ssl_options,
            locale="en_US"
        )

    def subscribe(self):
        logger.info("\n### STARTING PIKA ###\n")
        with pika.BlockingConnection(parameters=self.params) as connection:
            # create channel to the broker
            channel = connection.channel()
            # bind the keys we need to the exchange and predefined queues

            # NOTE: this is **not** necessary if the bindings are defined by hand in the UI
            # passively declare the exchange (check for existence), in this case a topic exchange
            # again, not needed in case of existing queue bindings
            channel.exchange_declare(
                self.config.exchange, exchange_type="topic", passive=True
            )
            channel.queue_declare(queue=self.config.queue, passive=True)

            for key in BINDING_KEYS.keys():
                channel.queue_bind(
                    queue=self.config.queue,
                    exchange=self.config.exchange,
                    routing_key=key
                )

            channel.basic_consume(
                queue=self.config.queue,
                on_message_callback=self.callback,
                auto_ack=True
            )
            channel.start_consuming()

    def publish(self, message, routing_key, message_id):

        with pika.BlockingConnection(parameters=self.params) as connection:
            # create channel to the broker
            channel = connection.channel()
            # declare the exchange to use passively (just checks it exists), in this case a topic exchange
            channel.exchange_declare(
                self.config.exchange, exchange_type="topic", passive=True
            )

            properties = BasicProperties(
                content_type="application/json",
                content_encoding="utf-8",
                delivery_mode=2,
                app_id=self.config.app_id,
                user_id=self.config.username,
                message_id=message_id,
            )
            channel.basic_publish(
                exchange=self.config.exchange,
                routing_key=routing_key,
                properties=properties,
                body=message,
            )

    @staticmethod
    def callback(
        channel, method: Method, properties: BasicProperties, body: str
    ):
        logger.info(f"[{datetime.now()}] Received {method.routing_key}:")
        logger.info("properties: ")
        logger.info(properties)
        logger.info("body: ")
        logger.info(body)

        unhandled_method = True
        for pattern, handlers in BINDING_KEYS.items():
            if re.match(binding_key_to_regex(pattern), method.routing_key):
                unhandled_method = False
                for handler in handlers:
                    try:
                        callable = import_callable(handler)
                        result = callable(
                            json.loads(body), properties=properties
                        )
                        if result:
                            logger.info(result)
                    except Exception as e:
                        logger.error(e)

        if unhandled_method:
            logger.error(
                f"'{method.routing_key}' does not match any BINDING_KEYS"
            )
