"""The RabbitMQRequestHandler wraps RabbitMQ use into a request handler, with
methods to speed the development of publishing RabbitMQ messages.

Example configuration:

    Application:
      rabbitmq:
        host: rabbitmq1
        virtual_host: my_web_app
        username: tinman
        password: tornado

"""
import logging
import pika
from pika.adapters import tornado_connection
from tornado import web

LOGGER = logging.getLogger(__name__)

from tinman import exceptions

message_stack = list()
pending_rabbitmq_connection = None
rabbitmq_connection = None


class RabbitMQRequestHandler(web.RequestHandler):
    """The request handler will connect to RabbitMQ on the first request,
    buffering any messages that need to be published until the Channel to
    RabbitMQ is opened, sending the stack of previously buffered messages at
    that time. If RabbitMQ closes it's connection to the app at any point, a
    connection attempt will be made on the next request.

    Expects configuration in the YAML file under a "rabbitmq" node. All of the
    configuration values are optional but username and password:

        host: Hostname, defaults to localhost if omitted
        port: RabbitMQ port, defaults to 5672 if omitted
        virtual_host: The virtual host, defaults to / if omitted
        username: The username to connect with
        password: The password to connect with
        channel_max: Maximum number of channels to allow, defaults to 0
        frame_max: The maximum byte size for an AMQP frame, defaults to 131072
        heartbeat_interval: Heartbeat interval, defaults to 0 (Off)
        ssl: Enable SSL, defaults to False
        ssl_options: Arguments passed to ssl.wrap_socket as described at
                     http://docs.python.org/dev/library/ssl.html
        connection_attempts: Maximum number of retry attempts, defaults to 1
        retry_delay: Time to wait in seconds between attempts, defaults to 2
        socket_timeout: Use for high latency networks, defaults to 0.25
        locale: Set the connection locale value, defaults to en_US

    """
    CHANNEL = 'rabbitmq_channel'
    CONNECTION = 'rabbitmq_connection'

    def _add_to_publish_stack(self, exchange, routing_key, message, properties):
        """Temporarily add the message to the stack to publish to RabbitMQ

        :param str exchange: The exchange to publish to
        :param str routing_key: The routing key to publish with
        :param str message: The message body
        :param pika.BasicProperties: The message properties

        """
        global message_stack
        message_stack.append((exchange, routing_key, message, properties))

    def _connect_to_rabbitmq(self):
        """Connect to RabbitMQ and assign a local attribute"""
        global pending_rabbitmq_connection, rabbitmq_connection
        if not rabbitmq_connection:
            LOGGER.info('Creating a new RabbitMQ connection')
            pending_rabbitmq_connection = self._new_rabbitmq_connection()

    def _new_message_properties(self, content_type=None, content_encoding=None,
                                headers=None, delivery_mode=None, priority=None,
                                correlation_id=None, reply_to=None,
                                expiration=None, message_id=None,
                                timestamp=None, message_type=None, user_id=None,
                                app_id=None):
        """Create a BasicProperties object, with the properties specified

        :param str content_type: MIME content type
        :param str content_encoding: MIME content encoding
        :param dict headers: Message header field table
        :param int delivery_mode: Non-persistent (1) or persistent (2)
        :param int priority: Message priority, 0 to 9
        :param str correlation_id: Application correlation identifier
        :param str reply_to: Address to reply to
        :param str expiration: Message expiration specification
        :param str message_id: Application message identifier
        :param int timestamp: Message timestamp
        :param str message_type: Message type name
        :param str user_id: Creating user id
        :param str app_id: Creating application id
        :rtype: pika.BasicProperties

        """
        return pika.BasicProperties(content_type, content_encoding, headers,
                                    delivery_mode, priority, correlation_id,
                                    reply_to, expiration, message_id, timestamp,
                                    message_type, user_id, app_id)

    def _new_rabbitmq_connection(self):
        """Return a connection to RabbitMQ via the pika.Connection object.
        When RabbitMQ is connected, on_rabbitmq_open will be called.

        :rtype: pika.adapters.tornado_connection.TornadoConnection

        """
        return tornado_connection.TornadoConnection(self._rabbitmq_parameters,
                                                    self.on_rabbitmq_conn_open)

    def _publish_deferred_messages(self):
        """Called when pika is connected and has a channel open to publish
        any requests buffered.

        """
        global message_stack
        if not self._rabbitmq_is_closed and message_stack:
            LOGGER.info('Publishing %i deferred message(s)', len(message_stack))
            while message_stack:
                self._publish_message(*message_stack.pop())

    def _publish_message(self, exchange, routing_key, message, properties):
        """Publish the message to RabbitMQ

        :param str exchange: The exchange to publish to
        :param str routing_key: The routing key to publish with
        :param str message: The message body
        :param pika.BasicProperties: The message properties

        """
        if self._rabbitmq_is_closed or not self._rabbitmq_channel:
            LOGGER.warning('Temporarily buffering message to publish')
            self._add_to_publish_stack(exchange, routing_key,
                                       message, properties)
            return
        self._rabbitmq_channel.basic_publish(exchange, routing_key,
                                             message, properties)

    @property
    def _rabbitmq_config(self):
        """Return the RabbitMQ configuration dictionary.

        :rtype: dict

        """
        config = self.application.settings.get('rabbitmq')
        if not config:
            raise exceptions.ConfigurationException('rabbitmq')
        return config

    @property
    def _rabbitmq_channel(self):
        """Return the Pika channel from the tinman object assignment.

        :rtype: pika.channel.Channel

        """
        return getattr(self.application.attributes, self.CHANNEL, None)

    @property
    def _rabbitmq_is_closed(self):
        """Returns True if the pika connection to RabbitMQ is closed.

        :rtype: bool

        """
        global rabbitmq_connection
        return not rabbitmq_connection and not pending_rabbitmq_connection

    @property
    def _rabbitmq_parameters(self):
        """Return a pika ConnectionParameters object using the configuration
        from the configuration service. The configuration dictionary should
        match the parameters for pika.connection.ConnectionParameters and
        include an extra username and password variable.

        :rtype: pika.ConnectionParameters

        """
        kwargs = dict(self._rabbitmq_config)
        kwargs['credentials'] =  pika.PlainCredentials(kwargs['username'],
                                                       kwargs['password'])
        for key in ['username', 'password']:
            del kwargs[key]
        return pika.ConnectionParameters(**kwargs)

    def _set_rabbitmq_channel(self, channel):
        """Assign the channel object to the tinman global object.

        :param pika.channel.Channel channel: The pika channel

        """
        setattr(self.application.attributes, self.CHANNEL, channel)

    def on_rabbitmq_close(self, reply_code, reply_text):
        """Called when RabbitMQ has been connected to.

        :param int reply_code: The code for the disconnect
        :param str reply_text: The disconnect reason

        """
        global rabbitmq_connection
        LOGGER.warning('RabbitMQ has disconnected (%s): %s',
                       reply_code, reply_text)
        rabbitmq_connection = None
        self._set_rabbitmq_channel(None)
        self._connect_to_rabbitmq()

    def on_rabbitmq_conn_open(self, connection):
        """Called when RabbitMQ has been connected to.

        :param pika.connection.Connection connection: The pika connection

        """
        global pending_rabbitmq_connection, rabbitmq_connection
        LOGGER.info('RabbitMQ has connected')
        rabbitmq_connection = connection
        rabbitmq_connection.add_on_close_callback(self.on_rabbitmq_close)
        rabbitmq_connection.channel(self.on_rabbitmq_channel_open)
        pending_rabbitmq_connection = None

    def on_rabbitmq_channel_open(self, channel):
        """Called when the RabbitMQ accepts the channel open request.

        :param pika.channel.Channel channel: The channel opened with RabbitMQ

        """
        LOGGER.info('Channel %i is opened for communication with RabbitMQ',
                    channel.channel_number)
        self._set_rabbitmq_channel(channel)
        self._publish_deferred_messages()

    def prepare(self):
        """Prepare the handler, ensuring RabbitMQ is connected or start a new
        connection attempt.

        """
        super(RabbitMQRequestHandler, self).prepare()
        if self._rabbitmq_is_closed:
            self._connect_to_rabbitmq()
