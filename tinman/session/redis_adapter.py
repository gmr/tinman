"""
The Redis Session Adapter

"""
import json
import logging
from tornado import gen
from tinman import session
import tornadoredis

REDIS_CLIENT = None
LOGGER = logging.getLogger(__name__)


class RedisSessionAdapter(session.SessionAdapter):
    """Stores session data in redis. Configuration values that can be set:

        host, port, db

    If the host, port and db are not set, the

    """
    FORMAT = 'tinman:session:%s'
    REDIS_HOST = 'localhost'
    REDIS_PORT = 6379
    REDIS_DB = 0

    def __init__(self, session_id=None, configuration=None,
                 duration=session.DEFAULT_DURATION):
        """Create a session adapter for the base URL specified, creating a new
        session if no session id is passed in.

        :param str session_id: The current session id if once has been started
        :param dict configuration: Session storage configuration
        :param int duration: The session duration for storage retention

        """
        super(RedisSessionAdapter, self).__init__(session_id, configuration,
                                                  duration)
        LOGGER.debug('Settings: %r', configuration)
        global REDIS_CLIENT
        if REDIS_CLIENT is None:
            REDIS_CLIENT = self._connect_to_redis()
        self._client = REDIS_CLIENT

    def _connect_to_redis(self):
        LOGGER.debug('Connecting to redis')
        return tornadoredis.Client(**self._redis_connection_settings)

    @gen.engine
    def _fetch_session_data(self):
        data = yield gen.Task(self._client.get, self._session_key)
        self.__dict__['data'] = json.loads(data) if data else dict()
        LOGGER.debug('Data loaded: %r', self.__dict__['data'])

    def _load_session_data(self):
        """Extend to the load the session from storage

        :rtype: dict

        """
        self._fetch_session_data()
        return dict()

    @property
    def _redis_connection_settings(self):
        LOGGER.debug('Redis arguments')
        settings = self._config.get('redis')
        return {'host': settings.get('host', self.REDIS_HOST),
                'port': settings.get('port', self.REDIS_PORT),
                'selected_db': settings.get('db', self.REDIS_DB)}

    @property
    def _session_key(self):
        return self.FORMAT % self.id

    @gen.engine
    def _store_session_data(self):
        yield gen.Task(self._client.set, self._session_key,
                       json.dumps(self.__dict__['data']))
        yield gen.Task(self._client.expire, self._session_key, self._duration)
        LOGGER.debug('Session saved')

    def delete(self):
        """Remove the session data from storage, clearing any session values"""
        self.clear()
        yield gen.Task(self._client.delete, self._session_key)

    def save(self):
        """Store the session for later retrieval

        :raises: IOError

        """
        self._store_session_data()
