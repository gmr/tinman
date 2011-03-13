"""
Tinman Cache Module
"""
__author__ = "Gavin M. Roy"
__email__ = "gmr@myyearbook.com"
__date__ = "2010-03-10"
__version__ = 0.2

from logging import debug

# Module wide dictionary to hold the cached values in
local_cache = dict()


# Cache Decorator
def memoize(fn):

    def wrapper(*args):
        # Our module wide local_cache
        global local_cache

        # Get the class name for the key
        key = repr(args[0])

        # Add the arguments to the key
        for value in args[1:]:
            key += ':%s' % str(value)

        debug('memoize: %s' % key)
        if key in local_cache:
            debug('memoize hit: %s' % key)
            return local_cache[key]

        # Call and return the original function
        value = fn(*args)

        # Set the Value
        debug('memoize set: %s' % key)
        local_cache[key] = value

        # Return the value
        return value

    return wrapper


def flush():
    """
    Flush all of the attributes in the cache
    """
    global local_cache
    local_cache = dict()
