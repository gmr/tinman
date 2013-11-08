"""
Mixin handlers adding various different types of functionality

"""
from tornado import escape
from tornado import gen
import logging
from tornado import web

from tinman.handlers import base
from tinman import config

LOGGER = logging.getLogger(__name__)


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

    # Data attributes to strip from the model
    STRIP_ATTRIBUTES = []

    # Core Tornado Methods

    def initialize(self):
        super(ModelAPIMixin, self).initialize()
        self.model = None

    @web.asynchronous
    @gen.engine
    def delete(self, *args, **kwargs):
        # Create the model and fetch its data
        self.model = self.get_model(kwargs.get('id'))
        result = yield self.model.fetch()

        # If model is not found, return 404
        if not result:
            self.not_found()
            return

        # Stub to check for read permissions
        if not self.has_write_permission():
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

        # Add the headers and return the content as JSON
        self.add_headers()
        self.finish(self.model_json())

    @web.asynchronous
    @gen.engine
    def post(self, *args, **kwargs):
        self.initialize_post()
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
        self.initialize_put(kwargs.get('id'))
        changed = False
        for key, value in self.model.iteritems():
            if self.json_arguments.get(key) != value:
                changed = True
                self.model.set(key, self.json_arguments.get(key))

        if not changed:
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
    def has_read_permission(self):
        """Extend this method to implement custom authentication checking
        for your data APIs.

        :rtype: bool

        """
        return True

    def has_write_permission(self):
        """Extend this method to implement custom authentication checking
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
        for key in self.STRIP_ATTRIBUTES:
            del output[key]
        return web.utf8(escape.json_encode(output))

    def not_found(self):
        self.set_status(404, self.status_message('Not Found'))
        self.finish()

    def permission_denied(self, message=None):
        self.set_status(404, self.status_message(message or
                                                 'Permission Denied'))
        self.finish()

    def status_message(self, message):
        return self.model.__class__.__name__ + ' ' + message


class RedisModelAPIMixin(ModelAPIMixin, RedisMixin):
    """Use for Model API support with Redis"""
    def get_model(self, *args, **kwargs):
        kwargs['redis_client'] = RedisMixin._redis_client
        return self.MODEL(*args, **kwargs)
