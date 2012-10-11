"""The RedisRequestHandler uses tornado-redis to support Redis. It will
auto-establish a single redis connection when initializing the connection.

"""
import logging
import tornadoredis
from tornado import web

LOGGER = logging.getLogger(__name__)


class RedisRequestHandler(web.RequestHandler):
    """This request handler will connect to Redis on initialize if the
    connection is not previously set.

    """
    REDIS_CLIENT = 'redis'
    REDIS_HOST = 'localhost'
    REDIS_PORT = 6379
    REDIS_DB = 0

    def prepare(self):
        super(RedisRequestHandler, self).prepare()
        if not self._has_redis_client:
            self._set_redis_client(self._connect_to_redis())

    @property
    def _has_redis_client(self):
        return hasattr(self.application.tinman, self.REDIS_CLIENT)

    def _connect_to_redis(self):
        LOGGER.debug('Connecting to redis: %r', self._redis_connection_settings)
        client = tornadoredis.Client(**self._redis_connection_settings)
        client.connect()
        return client

    @property
    def _redis_connection_settings(self):
        return {'host': self._redis_settings.get('host', self.REDIS_HOST),
                'port': self._redis_settings.get('port', self.REDIS_PORT),
                'selected_db': self._redis_settings.get('db', self.REDIS_DB)}

    @property
    def _redis_settings(self):
        LOGGER.debug('Redis settings')
        return self.application.settings.get('redis', dict())

    def _set_redis_client(self, client):
        setattr(self.application.tinman, self.REDIS_CLIENT, client)

    @property
    def redis_client(self):
        LOGGER.debug('Returning redis client')
        return getattr(self.application.tinman, self.REDIS_CLIENT, None)

