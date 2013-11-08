"""
Tinman session classes for the management of session data

"""
from tornado import concurrent
import logging
import os
from os import path
import tempfile
import time
import uuid

from tinman import config
from tinman import exceptions
from tinman import mapping

LOGGER = logging.getLogger(__name__)


class Session(mapping.Mapping):
    """Session provides a base interface for session management and should be
    extended by storage objects that are used by the SessionHandlerMixin.

    """
    id = None
    ip_address = None
    last_request_at = None
    last_request_uri = None

    def __init__(self, session_id=None, duration=3600, settings=None):
        """Create a new session instance. If no id is passed in, a new ID is
        created. If an id is passed in, load the session data from storage.

        :param str session_id: The session ID
        :param dict settings: Session object configuration

        """
        super(Session, self).__init__()
        self._duration = duration
        self._settings = settings or dict()
        self.id = session_id or str(uuid.uuid4())

    def fetch(self):
        """Fetch the contents of the session from storage.

        :raises: NotImplementedError

        """
        raise NotImplementedError

    def delete(self):
        """Extend to the delete the session from storage

        :raises: NotImplementedError

        """
        raise NotImplementedError

    def save(self):
        """Save the session for later retrieval

        :raises: NotImplementedError

        """
        raise NotImplementedError


class FileSession(Session):
    """Session data is stored on disk using the FileSession object.

    Configuration in the application settings is as follows::

        Application:
          session:
            adapter:
              name: file
              cleanup: false
              directory: /tmp/sessions
            cookie:
              name: session
              duration: 3600

    """
    DEFAULT_SUBDIR = 'tinman'

    def __init__(self, session_id=None, duration=None, settings=None):
        """Create a new session instance. If no id is passed in, a new ID is
        created. If an id is passed in, load the session data from storage.

        :param str session_id: The session ID
        :param dict settings: Session object configuration

        """
        super(FileSession, self).__init__(session_id, duration, settings)
        self._storage_dir = self._setup_storage_dir()
        if settings.get('cleanup', True):
            self._cleanup()

    def fetch(self):
        """Fetch the contents of the session from storage.

        :raises: NotImplementedError

        """
        raise NotImplementedError

    def delete(self):
        """Extend to the delete the session from storage

        """
        self.clear()
        if os.path.isfile(self._filename):
            os.unlink(self._filename)
        else:
            LOGGER.debug('Session file did not exist: %s', self._filename)

    def save(self):
        """Save the session for later retrieval

        :raises: IOError

        """
        try:
            with open(self._filename, 'wb') as session_file:
                session_file.write(self.dumps())
        except IOError as error:
            LOGGER.error('Session file error: %s', error)
            raise error

    def _cleanup(self):
        """Remove any stale files from the session storage directory"""
        for filename in os.listdir(self._storage_dir):
            file_path = path.join(self._storage_dir, filename)
            file_stat = os.stat(file_path)
            evaluate = max(file_stat.st_ctime, file_stat.st_mtime)
            if evaluate + self._duration < time.time():
                LOGGER.debug('Removing stale file: %s', file_path)
                os.unlink(file_path)

    @property
    def _default_path(self):
        """Return the default path for session data

        :rtype: str

        """
        return path.join(tempfile.gettempdir(), self.DEFAULT_SUBDIR)

    @property
    def _filename(self):
        """Returns the filename for the session file.

        :rtype: str

        """
        return path.join(self._storage_dir, self.id)

    @staticmethod
    def _make_path(dir_path):
        """Create the full path specified.

        :param str dir_path: The path to make

        """
        os.makedirs(dir_path, 0x755)

    def _setup_storage_dir(self):
        """Setup the storage directory path value and ensure the path exists.

        :rtype: str
        :raises: tinman.exceptions.ConfigurationException

        """
        dir_path = self._settings.get(config.DIRECTORY)
        if dir_path is None:
            dir_path = self._default_path
            if not os.path.exists(dir_path):
                self._make_path(dir_path)
        else:
            dir_path = path.abspath(dir_path)
            if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
                raise exceptions.ConfigurationException(self.__class__.__name__,
                                                        config.DIRECTORY)
        return dir_path.rstrip('/')


class RedisSession(Session):
    """Using the RedisSession object, session data is stored in a Redis database
    using the tornadoredis client library.

    Example configuration in the application settings is as follows::

        Application:
          session:
            adapter:
              name: redis
              host: localhost
              port: 6379
              db: 2
            cookie:
              name: session
              duration: 3600

    """
    _redis_client = None
    REDIS_DB = 2
    REDIS_HOST = 'localhost'
    REDIS_PORT = 6379

    def __init__(self, session_id, duration=None, settings=None):
        """Create a new redis session instance. If no id is passed in, a
        new ID is created. If an id is passed in, load the session data from
        storage.

        :param str session_id: The session ID
        :param dict config: Session object configuration

        """
        if not RedisSession._redis_client:
            RedisSession._redis_connect(settings)
        super(RedisSession, self).__init__(session_id, duration, settings)

    @property
    def _key(self):
        return 's:%s' % self.id

    @classmethod
    def _redis_connect(cls, settings):
        """Connect to redis and assign the client to the RedisSession class
        so that it is globally available in this process.

        :param dict settings: The redis session configuration

        """
        if 'tornadoredis' not in globals():
            import tornadoredis
        kwargs = {'host': settings.get('host', cls.REDIS_HOST),
                  'port': settings.get('port', cls.REDIS_PORT),
                  'selected_db': settings.get('db', cls.REDIS_DB)}
        LOGGER.info('Connecting to %(host)s:%(port)s DB %(selected_db)s',
                    kwargs)
        cls._redis_client = tornadoredis.Client(**kwargs)
        cls._redis_client.connect()

    @concurrent.return_future
    def delete(self, callback):
        """Delete the item from storage

        :param method callback: The callback method to invoke when done

        """
        LOGGER.debug('Deleting session %s', self.id)
        def on_result(value):
            callback(True)
        RedisSession._redis_client.delete(self._key, on_result)
        self.clear()

    @concurrent.return_future
    def fetch(self, callback):
        """Fetch the data for the model from Redis and assign the values.

        :param method callback: The callback method to invoke when done

        """
        def on_result(value):
            if value:
                self.loads(value)
            callback(bool(value))
        RedisSession._redis_client.get(self._key, on_result)

    @concurrent.return_future
    def save(self, callback):
        """Store the session data in redis

        :param method callback: The callback method to invoke when done

        """
        LOGGER.debug('Saving session %s', self.id)
        def on_result(value):
            callback(True)
        RedisSession._redis_client.set(self._key, self.dumps(), on_result)

