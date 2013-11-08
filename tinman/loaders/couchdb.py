"""This module is deprecated"""
import warnings

warnings.warn('tinman.loaders.couchdb moved to tinman.couchdb',
              DeprecationWarning, stacklevel=2)

from tinman import couchdb
