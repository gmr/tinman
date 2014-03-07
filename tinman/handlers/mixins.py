"""
Mixin handlers adding various different types of functionality

"""
import socket
from tornado import escape
from tornado import gen
import logging
from tornado import web

from tinman.handlers import base
from tinman import config

LOGGER = logging.getLogger(__name__)


class StatsdMixin(base.RequestHandler):
    """Increments a counter and adds timing data to statsd for each request.

    Example key format:

        tornado.web.RequestHandler.GET.200

    Additionally adds methods for talking to statsd via the request handler.

    By default, it will talk to statsd on localhost. To configure the statsd
    server address, add a statsd staza to the application configuration:

    Application:
      statsd:
        host: 192.168.1.2
        port: 8125
    
    """
    STATSD_HOST = '127.0.0.1'
    STATSD_PORT = 8125

    def __init__(self, application, request, **kwargs):
        super(StatsdMixin, self).__init__(application, request, **kwargs)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    @property
    def _statsd_address(self):
        """Return a tuple of host and port for the statsd server to send
        stats to.

        :return: tuple(host, port)

        """
        return (self.application.settings.get('statsd',
                                              {}).get('host',
                                                      self.STATSD_HOST),
                self.application.settings.get('statsd',
                                              {}).get('port',
                                                      self.STATSD_PORT))

    def _statsd_send(self, value):
        """Send the specified value to the statsd daemon via UDP without a
        direct socket connection.

        :param str value: The properly formatted statsd counter value

        """
        self.socket.sendto(value, self._statsd_address)

    def on_finish(self):
        """Invoked once the request has been finished. Increment a counter
        created in the format:

            package[.module].Class.METHOD.STATUS
            tornado.web.RequestHandler.GET.200

        """
        super(StatsdMixin, self).on_finish()
        key = '%s.%s.%s.%s' % (self.__module__,
                               self.__class__.__name__,
                               self.request.method, self._status_code)
        LOGGER.info('Processing %s', key)
        self.statsd_incr(key)
        self.statsd_add_timing(key, self.request.request_time() * 1000)

    def statsd_incr(self, name, value=1):
        """Increment a statsd counter by the specified value.

        :param str name: The counter name to increment
        :param int|float value: The value to increment by

        """
        self._statsd_send('%s:%s|c' % (name, value))

    def statsd_set_gauge(self, name, value):
        """Set a gauge in statsd for the specified name and value.

        :param str name: The gauge name to increment
        :param int|float value: The gauge value

        """
        self._statsd_send('%s:%s|g' % (name, value))

    def statsd_add_timing(self, name, value):
        """Add a time value in statsd for the specified name

        :param str name: The timing name to add a sample to
        :param int|float value: The time value

        """
        self._statsd_send('%s:%s|ms' % (name, value))


class RedisMixin(base.RequestHandler):
    """This request web will connect to Redis on initialize if the
    connection is not previously set. Uses the asynchronous tornadoredis
    library.

    Example use:

        @web.asynchronous
        @gen.engine
        def get(self, *args, **kwargs):
            value = self.redis.get('foo')

    """
    _redis_client = None
    _REDIS_HOST = 'localhost'
    _REDIS_PORT = 6379
    _REDIS_DB = 0

    @gen.coroutine
    def prepare(self):
        """Prepare RequestHandler requests, ensuring that there is a
        connected tornadoredis.Client object.

        """
        self._ensure_redis_client()
        super(RedisMixin, self).prepare()

    @property
    def redis(self):
        """Return a handle to the active redis client.

        :rtype: tornadoredis.Client

        """
        self._ensure_redis_client()
        return RedisMixin._redis_client

    def _ensure_redis_client(self):
        """Ensure the redis client has been created."""
        if not RedisMixin._redis_client:
            RedisMixin._redis_client = self._new_redis_client()

    def _new_redis_client(self):
        """Create a new redis client and assign it the class _redis_client
        attribute for reuse across requests.

        :rtype: tornadoredis.Client()

        """
        if 'tornadoredis' not in globals():
            import tornadoredis
        kwargs = self._redis_connection_settings()
        LOGGER.info('Connecting to %(host)s:%(port)s DB %(selected_db)s',
                    kwargs)
        return tornadoredis.Client(**kwargs)

    def _redis_connection_settings(self):
        """Return a dictionary of redis connection settings.

        """
        return {config.HOST: self.settings.get(config.HOST, self._REDIS_HOST),
                config.PORT: self.settings.get(config.PORT, self._REDIS_PORT),
                'selected_db': self.settings.get(config.DB, self._REDIS_DB)}


class ModelAPIMixin(base.RequestHandler):
    """The Model API Request Handler provides a simple RESTful API interface
    for access to Tinman data models.

    Set the MODEL attribute to the Model class for the web for basic,
    unauthenticated GET, DELETE, PUT, and POST behavior where PUT is

    """
    ACCEPT = [base.GET, base.HEAD, base.DELETE, base.PUT, base.POST]
    MODEL = None

    # Data attributes to replace in the model
    REPLACE_ATTRIBUTES = {'password': bool}

    # Data attributes to strip from the model
    STRIP_ATTRIBUTES = []

    # Core Tornado Methods

    def initialize(self):
        super(ModelAPIMixin, self).initialize()
        self.model = None

    @web.asynchronous
    @gen.engine
    def delete(self, *args, **kwargs):
        """Handle delete of an item

        :param args:
        :param kwargs:

        """
        # Create the model and fetch its data
        self.model = self.get_model(kwargs.get('id'))
        result = yield self.model.fetch()

        # If model is not found, return 404
        if not result:
            self.not_found()
            return

        # Stub to check for delete permissions
        if not self.has_delete_permission():
            self.permission_denied()
            return

        # Delete the model from its storage backend
        self.model.delete()

        # Set the status to request processed, no content returned
        self.set_status(204)
        self.finish()

    @web.asynchronous
    @gen.engine
    def head(self, *args, **kwargs):
        """Handle HEAD requests for the item

        :param args:
        :param kwargs:

        """
        # Create the model and fetch its data
        self.model = self.get_model(kwargs.get('id'))
        result = yield self.model.fetch()

        # If model is not found, return 404
        if not result:
            self.not_found()
            return

        # Stub to check for read permissions
        if not self.has_read_permission():
            self.permission_denied()
            return

        # Add the headers (etag, content-length), set the status
        self.add_headers()
        self.set_status(200)
        self.finish()

    @web.asynchronous
    @gen.engine
    def get(self, *args, **kwargs):
        """Handle reading of the model

        :param args:
        :param kwargs:

        """
        # Create the model and fetch its data
        self.model = self.get_model(kwargs.get('id'))
        result = yield self.model.fetch()

        # If model is not found, return 404
        if not result:
            LOGGER.debug('Not found')
            self.not_found()
            return

        # Stub to check for read permissions
        if not self.has_read_permission():
            LOGGER.debug('Permission denied')
            self.permission_denied()
            return

        # Add the headers and return the content as JSON
        self.add_headers()
        self.finish(self.model_json())

    @web.asynchronous
    @gen.engine
    def post(self, *args, **kwargs):
        """Handle creation of an item.

        :param args:
        :param kwargs:

        """
        self.initialize_post()

        # Don't allow the post if the poster does not have permission
        if not self.has_create_permission():
            LOGGER.debug('Does not have write_permission')
            self.set_status(403, self.status_message('Creation Forbidden'))
            self.finish()
            return

        result = yield self.model.save()
        if result:
            self.set_status(201, self.status_message('Created'))
            self.add_headers()
            self.finish(self.model.as_dict())
        else:
            self.set_status(507, self.status_message('Creation Failed'))
            self.finish()

    @web.asynchronous
    @gen.engine
    def put(self, *args, **kwargs):
        """Handle updates of an item.

        :param args:
        :param kwargs:

        """
        self.initialize_put(kwargs.get('id'))

        if not self.has_update_permission():
            self.set_status(403, self.status_message('Creation Forbidden'))
            self.finish()
            return

        for key, value in self.model.items():
            if self.json_arguments.get(key) != value:
                self.model.set(key, self.json_arguments.get(key))

        if not self.model.dirty:
            self.set_status(431, self.status_message('No changes made'))
            self.finish(self.model.as_dict())
            return

        result = yield self.model.save()
        if result:
            self.set_status(200, self.status_message('Updated'))
        else:
            self.set_status(507, self.status_message('Update Failed'))
        self.add_headers()
        self.finish(self.model.as_dict())

    # Methods to Extend

    def has_create_permission(self):
        """Extend this method to implement custom permission checking
        for your data APIs.

        :rtype: bool

        """
        return True

    def has_delete_permission(self):
        """Extend this method to implement custom permission checking
        for your data APIs.

        :rtype: bool

        """
        return True

    def has_read_permission(self):
        """Extend this method to implement custom permission checking
        for your data APIs.

        :rtype: bool

        """
        return True

    def has_update_permission(self):
        """Extend this method to implement custom permission checking
        for your data APIs.

        :rtype: bool

        """
        return True

    def initialize_post(self):
        """Invoked by the ModelAPIRequestHandler.post method prior to taking
        any action.

        """
        self.model = self.get_model()
        for key in self.model.keys():
            self.model.set(key, self.json_arguments.get(key))

    def initialize_put(self, item_id):
        """Invoked by the ModelAPIRequestHandler.put method prior to taking
        any action.

        """
        self.model = self.get_model(item_id)

    # Model API Methods

    def add_etag(self):
        self.set_header('Etag', '"%s"' % self.model.sha1())

    def add_content_length(self):
        self.set_header('Content-Length', len(self.model_json()))

    def add_headers(self):
        self.add_etag()
        self.add_content_length()

    def get_model(self, *args, **kwargs):
        return self.MODEL(*args, **kwargs)

    def model_json(self):
        output = self.model.as_dict()
        for key in self.REPLACE_ATTRIBUTES:
            output[key] = self.REPLACE_ATTRIBUTES[key](output[key])
        for key in self.STRIP_ATTRIBUTES:
            del output[key]
        return web.utf8(escape.json_encode(output))

    def not_found(self):
        self.set_status(404, self.status_message('Not Found'))
        self.finish()

    def permission_denied(self, message=None):
        self.set_status(403, self.status_message(message or
                                                 'Permission Denied'))
        self.finish()

    def status_message(self, message):
        return self.model.__class__.__name__ + ' ' + message


class RedisModelAPIMixin(ModelAPIMixin, RedisMixin):
    """Use for Model API support with Redis"""
    def get_model(self, *args, **kwargs):
        kwargs['redis_client'] = RedisMixin._redis_client
        return self.MODEL(*args, **kwargs)
