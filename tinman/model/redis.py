"""
Tinman Redis Storage Model Base classes

"""
import base64
from tornado import gen
import logging
import tornadoredis

from tinman.model import base

LOGGER = logging.getLogger(__name__)


class AsyncRedisModel(base.StorageModel):
    """A model base class that uses Redis for the storage backend. Uses the
    asynchronous tornadoredis client. If you assign a value to the _ttl
    attribute, that _ttl value will be used to set the expiraiton of the
    data in redis.

    :param str item_id: The id for the data item
    :param tornadoredis.Client: The already created tornadoredis client

    """
    _ttl = None

    def __init__(self, item_id=None, **kwargs):
        if 'redis_client' not in kwargs:
            raise ValueError('redis_client must be passed in')
        self._redis_client = kwargs['redis_client']

        # The parent will attempt to fetch the value if item_id is set
        super(AsyncRedisModel, self).__init__(item_id, **kwargs)

    @property
    def _key(self):
        """Return a storage key for Redis that consists of the class name of
        the model and its id joined by :.

        :rtype: str

        """
        return '%s:%s' % (self.__class__.__name__, self.id)

    @gen.coroutine
    def delete(self):
        """Delete the item from storage

        """
        yield gen.Task(self._redis_client.delete, self._key)

    @gen.coroutine
    def fetch(self):
        """Fetch the data for the model from storage and assign the values.

        :rtype: bool

        """
        raw = yield gen.Task(self._redis_client.get, self._key)
        if raw:
            self.loads(base64.b64decode(raw))
            yield True
        yield False

    @gen.coroutine
    def save(self):
        """Store the model. This method is defined by a model storage mixin form
        tinman.model.mixins.

        :yields: bool

        """
        pipeline = self._redis_client.pipeline()
        pipeline.set(self._key, base64.b64encode(self.dumps()))
        if self._ttl:
            pipeline.expire(self._key, self._ttl)
        result = yield gen.Task(pipeline.execute)
        raise gen.Return(all(result))
