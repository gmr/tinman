"""The RedisRequestHandler uses tornado-redis to support Redis. It will
auto-establish a single redis connection when initializing the connection.

"""
import logging
from tornado import web

LOGGER = logging.getLogger(__name__)


class RedisRequestHandler(web.RequestHandler):
    """This request handler will connect to Redis on initialize if the
    connection is not previously set. This handler uses the redis library for
    synchronous redis use.

    """
    CONFIG_DB = 'db'
    REDIS = 'redis'
    REDIS_HOST = 'localhost'
    REDIS_PORT = 6379
    REDIS_DB = 0

    def _new_redis_client(self):
        """Create a new redis client and assign it to the application.attributes
        object for reuse later.

        """
        if 'redis' not in globals():
            import redis
        LOGGER.info('Creating new Redis instance')
        settings = self._redis_settings
        LOGGER.debug('Connecting to redis: %r', settings)
        client = redis.Redis(**settings)
        self.application.attributes.add(self.REDIS, client)

    @property
    def _redis_settings(self):
        """Return the Redis settings from configuration as a dict, defaulting
        to localhost:6379:0 if it's not set in configuration. The dict format
        is set to be passed as kwargs into the Client object.

        :rtype: dict

        """
        settings = self.application.settings.get('redis', dict())
        return {'host': settings.get('host', self.REDIS_HOST),
                'port': settings.get('port', self.REDIS_PORT),
                self.CONFIG_DB: settings.get('db', self.REDIS_DB)}

    def prepare(self):
        """Prepare RedisRequestHandler requests, ensuring that there is a
        connected tornadoredis.Client object.

        """
        super(RedisRequestHandler, self).prepare()
        if self.REDIS not in self.application.attributes:
            self._new_redis_client()

    @property
    def redis(self):
        """Return a handle to the active redis client.

        :rtype: tornadoredis.Redis

        """
        if self.REDIS not in self.application.attributes:
            self._new_redis_client()
        return self.application.attributes.redis


class AsynchronousRedisRequestHandler(RedisRequestHandler):
    """This request handler will connect to Redis on initialize if the
    connection is not previously set and uses the tornado-redis library for
    asynchronous use.

    """
    CONFIG_DB = 'selected_db'

    def _new_redis_client(self):
        """Create a new redis client and assign it to the application.attributes
        object for reuse later.

        """
        if 'tornadoredis' not in globals():
            import tornadoredis
        LOGGER.info('Creating new Redis instance')
        settings = self._redis_settings
        LOGGER.debug('Connecting to redis: %r', settings)
        client = tornadoredis.Client(**settings)
        client.connect()
        self.application.attributes.add(self.REDIS, client)
