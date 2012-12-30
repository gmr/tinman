"""The RedisRequestHandler uses tornado-redis to support Redis. It will
auto-establish a single redis connection when initializing the connection.

"""
import logging
import tornadoredis
from tornado import web

LOGGER = logging.getLogger(__name__)

redis_client = None


class RedisRequestHandler(web.RequestHandler):
    """This request handler will connect to Redis on initialize if the
    connection is not previously set.

    """
    REDIS_HOST = 'localhost'
    REDIS_PORT = 6379
    REDIS_DB = 0

    def _connect_to_redis(self):
        """Connect to a Redis server returning the handle to the redis
        connection.

        :rtype: tornadoredis.Redis

        """
        settings = self._redis_settings
        LOGGER.debug('Connecting to redis: %r', settings)
        client = tornadoredis.Client(**settings)
        client.connect()
        return client

    def _new_redis_client(self):
        """Create a new redis client and assign it to the module level handle.

        """
        global redis_client
        redis_client = self._connect_to_redis()

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
                'selected_db': settings.get('db', self.REDIS_DB)}

    def prepare(self):
        """Prepare RedisRequestHandler requests, ensuring that there is a
        connected tornadoredis.Client object.

        """
        global redis_client
        super(RedisRequestHandler, self).prepare()
        if redis_client is None or not redis_client.connection.connected:
            LOGGER.info('Creating new Redis instance')
            self._new_redis_client()

    @property
    def redis_client(self):
        """Return a handle to the active redis client.

        :rtype: tornadoredis.Redis

        """
        global redis_client
        return redis_client
