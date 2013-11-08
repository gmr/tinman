"""
Deprecated and moved into tornado.handlers.mixins

"""
import warnings
warnings.warn('tinman.handlers.redis_handlers moved to tinman.handlers.mixins',
              DeprecationWarning, stacklevel=2)

from tinman.handlers.mixins import RedisMixin as RedisRequestHandler
from tinman.handlers.mixins import RedisMixin as AsynchronousRedisRequestHandler
