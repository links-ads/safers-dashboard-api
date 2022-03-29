import json
import re
from importlib import import_module
from dataclasses import dataclass
from datetime import datetime

from django.conf import settings

import pika
from pika.frame import Method
from pika import BasicProperties

import ssl

#################
# routing table #
#################

BINDING_KEYS = {
    # a map of routing_key patterns to classes to run process_message w/ message
    "status.test.#": None,
    "event.social.*": 'safers.social.models.Tweet',
}


def binding_key_to_regex(binding_key):
    return binding_key.replace(".", "\.").replace("*", ".*").replace("#", "\d*")


def import_callable(path_or_callable):
    if hasattr(path_or_callable, '__call__'):
        return path_or_callable
    else:
        assert isinstance(path_or_callable, str)
        package, attr = path_or_callable.rsplit('.', 1)
        return getattr(import_module(package), attr)


##########
# config #
##########


@dataclass
class RMQConf:
    username: str
    password: str
    host: str
    queue: str = "qastro"
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
    encapsulates RabbitMQ functionality 
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
        print("\n### STARTING PIKA ###\n")
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
        for key, value in BINDING_KEYS.items():
            if value is not None and re.match(
                binding_key_to_regex(key), method.routing_key
            ):
                callable = import_callable(value)
                callable.process_message(
                    json.loads(body), properties=properties
                )

        print(dir(method))
        print(f"[{datetime.now()}] Received {method.routing_key}:")
        print("properties:")
        print(properties)
        print(body)