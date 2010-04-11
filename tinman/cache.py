#!/usr/bin/env python
"""
Tinman Cache Module
"""

__author__  = "Gavin M. Roy"
__email__   = "gavinmroy@gmail.com"
__date__    = "2010-03-10"
__version__ = 0.1

import logging
import memcache

client = False
config = False

# Cache Decorator
def memoize(fn):

    def wrapper(*args):
        global config, client

        # Get the class name for the key
        temp = str(args[0].__class__).split('.')
        class_name = temp[len(temp)-1:][0]

        # Set the base key
        key = '%s:%s:%s' % ( config['prefix'], str(class_name), str(fn.__name__) )

        # Add the arguments to the key
        for value in args[1:]:
            key += ':%s' % str(value)

        logging.debug('Cache Decorator Get for %s' % key)
        value = client.get(key)
        if value:
            logging.debug('Cache Decorator hit for %s' % key)
            return value

        # Call and return the original function
        value = fn(*args)

        # Set the Value
        logging.debug('Cache Decorator Set for %s' % key)
        client.set(key, value, config['duration'])

        # Return the value
        return value

    return wrapper


class Cache:

    def __init__(self, settings):
        global client
        client = memcache.Client(settings['connection'], debug=0)

    def delete(self, key):
        global connections
        logging.debug('Cache.delete for %s' % key)
        return client.delete(str(key))

    def get(self, key):
        global connections
        data = client.get(str(key))
        if data:
            logging.debug('Cache.hit for %s' % key)
        else:
            logging.debug('Cache miss for %s' % key)
        return data

    def set(self, key, value, duration):
        global connections
        logging.debug('Cache.set %s for %i' % (key, duration))
        return client.set(str(key), value, duration)

    def delete_decorator_item(self, classname, function, parameters):
        global config
        pass
