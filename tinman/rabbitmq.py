"""
Add RabbitMQ Support by adding a pika client that may be bound to the IO loop
instance
"""
__author__ = 'gmr'
__since__ = '6/8/11'

from . import __version__
import json
import logging
from pika import credentials
from pika import connection
from pika import spec
from pika.adapters import tornado_connection
import time


class RabbitMQ(object):

    DEFAULT_APP_ID = 'tinman'
    DEFAULT_DELIVERY_MODE = 1
    DEFAULT_ENCODING = 'UTF-8'

    def __init__(self, host, port, virtual_host, user, password):

        # Create a logger instance
        self._logger = logging.getLogger('tinman.rabbitmq')

        # We don't have a valid connection until the initial connect is done
        self._connection = None

        # We don't have a channel until we're connected
        self._channel = None

        # Set our app_id for publishing messages
        version = '%i.%i.%i' % __version__
        self.app_id = "%s/%s" % (RabbitMQ.DEFAULT_APP_ID, version)

        # Set our delivery mode for publishing messages
        self.delivery_mode = RabbitMQ.DEFAULT_DELIVERY_MODE

        # Set our encoding for publishing messages
        self.encoding = RabbitMQ.DEFAULT_ENCODING

        # Create our credentials
        creds = credentials.PlainCredentials(username=user, password=password)

        # Create the connection parameters
        self.params = connection.ConnectionParameters(host=host,
                                                      port=port,
                                                      virtual_host=virtual_host,
                                                      credentials=creds)

        # Create a new connection
        tornado_connection.TornadoConnection(self.params, self._on_connected)

    def _on_connected(self, connection):

        # Assign our connection to the object
        self._connection = connection

        # Create a channel to communicate on
        self._connection.channel(self._on_channel_opened)

        # Log our connection
        self._logger.info('Connected to RabbitMQ at %s:%i',
                          self.params.host, self.params.port)

    def _on_channel_opened(self, channel):

        # Create a channel to use
        self._channel = channel

        # Log the open channel
        self._logger.info('RabbitMQ channel opened at %s:%i',
                          self.params.host, self.params.port)

    def publish_message(self, exchange, routing_key, message,
                        mimetype='text/plain',
                        mandatory=False,
                        immediate=False):

        # Auto-JSON encode if it's not a string
        if not isinstance(message, basestring):
            message = json.dumps(message)
            mimetype = 'application/json'


        # Create the properties for the message
        props = spec.BasicProperties(content_type=mimetype,
                                     content_encoding=self.encoding,
                                     timestamp=time.time(),
                                     app_id=self.app_id,
                                     user_id=self.params.credentials.username)

        # Publish the message
        self._channel.basic_publish(exchange,
                                    routing_key,
                                    message,
                                    props,
                                    mandatory,
                                    immediate)
