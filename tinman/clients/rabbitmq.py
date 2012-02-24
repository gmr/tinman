"""
Add RabbitMQ Support by adding a pika client that may be bound to the IO loop
instance

"""
__author__ = 'Gavin M. Roy'
__email__ = 'gmr@myyearbook.com'
__since__ = '2011-06-06'


from tinman import __version__
import json
import logging
from pika import credentials
from pika import connection
from pika import spec
from pika.adapters import tornado_connection
import time


class RabbitMQ(object):
    """RabbitMQ object to facility easy integration with Pika. Currently
    only supports message publishing.

    """

    DEFAULT_APP_ID = 'tinman'
    DEFAULT_DELIVERY_MODE = 1
    DEFAULT_ENCODING = 'UTF-8'

    def __init__(self, host, port, virtual_host, user, password):
        """Construct our RabbitMQ object for use on the Tornado IOLoop

        :param host: RabbitMQ server host
        :type host: str
        :param port: RabbitMQ server port
        :type port: int
        :param virtual_host: RabbitMQ virtual host to use
        :type virtual_host: str
        :param user: RabbitMQ user to connect as
        :type user: str
        :param password: RabbitMQ user's password
        :type paassword: str

        """

        # Create a logger instance
        self._logger = logging.getLogger(__name__)

        # We don't have a valid connection until the initial connect is done
        self._connection = None

        # We don't have a channel until we're connected
        self._channel = None

        # Set our app_id for publishing messages
        self.app_id = "%s/%s" % (RabbitMQ.DEFAULT_APP_ID, __version__)

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
        """Called when a connection has opened.

        :param connection: RabbitMQ connection for raw communication
        :type connection: pika.connection.Connection

        """
        # Assign our connection to the object
        self._connection = connection

        # Create a channel to communicate on
        self._connection.channel(self._on_channel_opened)

        # Log our connection
        self._logger.info('Connected to RabbitMQ at %s:%i',
                          self.params.host, self.params.port)

    def _on_channel_opened(self, channel):
        """Called when a channel is opened.

        :param channel: RabbitMQ channel for commands and receiving messages
        :type channel: pika.channel.Channel
        """

        # Create a channel to use
        self._channel = channel

        # Log the open channel
        self._logger.info('RabbitMQ channel opened at %s:%i',
                          self.params.host, self.params.port)

    def publish_message(self, exchange, routing_key, message,
                        mimetype='text/plain',
                        mandatory=False,
                        immediate=False):
        """Publish a message to RabbitMQ. Auto-JSON encodes all non-string data
        types.

        :param exchange: RabbitMQ exchange to publish to.
        :type exchange: str
        :param routing_key: RabbitMQ publishing routing key
        :type routing_key: str
        :param mimetime: mimetype of the message
        :type mimetype: str
        :param mandatory: AMQP Basic.Publish mandatory flag
        :type mandatory: bool
        :param immediate: AMQP Basic.Publish immediate flag
        :type immediate: bool
        """

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
