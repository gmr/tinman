"""
Redis Session Adapter

"""
import logging
from tinman import session
import redis

LOGGER = logging.getLogger(__name__)


class RedisSessionAdapter(session.SessionAdapter):
    """Stores session data in redis. Configuration values that can be set:

        host, port, db

    If the host, port and db are not set, the

    """
    FORMAT = 'sess:%s'
    REDIS = 'session_redis'
    REDIS_HOST = 'localhost'
    REDIS_PORT = 6379
    REDIS_DB = 0

    def __init__(self, application, session_id=None, configuration=None,
                 duration=session.DEFAULT_DURATION, serializer=None):
        """Create a session adapter for the base URL specified, creating a new
        session if no session id is passed in.

        :param tinman.application.Application application: The Tinman app
        :param str session_id: The current session id if once has been started
        :param dict configuration: Session storage configuration
        :param int duration: The session duration for storage retention
        :type serializer: tinman.session.serializer.SessionSerializer

        """
        LOGGER.debug('Creating a new session adapter: %r', duration)
        super(RedisSessionAdapter, self).__init__(application, session_id,
                                                  configuration, duration,
                                                  serializer)
        self._setup_redis_client()
        LOGGER.debug('Duration: %r', self._duration)

    def delete(self):
        """Remove the session data from storage, clearing any session values"""
        yield
        self._redis.delete(self._session_key)
        self.clear()

    @property
    def redis_settings(self):
        """Return the Redis configuration settings

        :rtype: dict

        """
        return self._config.get('redis', dict())

    def save(self):
        """Store the session for later retrieval"""
        pipe = self._redis.pipeline()
        pipe.set(self._session_key, self._serialize())
        pipe.expire(self._session_key, self._duration)
        pipe.execute()
        LOGGER.debug('Session saved')

    def _load_session_data(self):
        """Extend to the load the session from storage

        :rtype: dict

        """
        data = self._redis.get(self._session_key)
        return self._deserialize(data) if data else dict()

    def _redis_client(self):
        """Return a newly constructed redis connection.

        :rtype: redis.Redis

        """
        LOGGER.debug(self._redis_config)
        return redis.Redis(**self._redis_config)

    @property
    def _redis_config(self):
        """Return the redis configuration as a dict.

        :return: dict

        """
        return {'host': self.redis_settings.get('host', self.REDIS_HOST),
                'port': self.redis_settings.get('port', self.REDIS_PORT),
                'db': self.redis_settings.get('db', self.REDIS_DB)}

    @property
    def _session_key(self):
        """Return the session key

        :rtype: str

        """
        return self.FORMAT % self.id

    def _setup_redis_client(self):
        """Setup a new redis client if it's not setup at the application
        attribute level, otherwise assign the attribute to an attribute of this
        object instance.

        """
        if self.REDIS not in self._application.attributes:
            self._redis = self._redis_client()
            self._application.attributes.add(self.REDIS, self._redis)
        else:
            self._redis = self._application.attributes.session_redis
