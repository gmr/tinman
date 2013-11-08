"""
Deprecated and moved into tornado.handlers.base

"""
import warnings
warnings.warn('tinman.handlers.session moved to tinman.handlers.base',
              DeprecationWarning, stacklevel=2)

from tinman.handlers.base import SessionRequestHandler
