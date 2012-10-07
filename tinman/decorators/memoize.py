"""
Tinman Cache Module
"""
__author__ = "Gavin M. Roy"
__email__ = "gmr@myyearbook.com"
__date__ = "2010-03-10"
__version__ = 0.2

from functools import wraps
from logging import debug

# Module wide dictionary to hold the cached values in
local_cache = dict()


def memoize_write(*args):

    # Append the value if the key exists, otherwise just set it
    if args[0].tinman_memoize_key in local_cache:
        debug('memoize append: %s' % args[0].tinman_memoize_key)
        local_cache[args[0].tinman_memoize_key] += args[1]
    else:
        debug('memoize set: %s' % args[0].tinman_memoize_key)
        local_cache[args[0].tinman_memoize_key] = args[1]

    # Call the monkey patched RequestHandler.write
    args[0]._write(args[1])


def memoize_finish(*args):

    # If they passed in a last chunk, run the write
    if len(args) > 1:
        memoize_write(args)

    # Un-Monkey-patch
    args[0].write = args[0]._write
    args[0].finish = args[0]._finish

    # Remove the monkey patched attributes
    del args[0]._write
    del args[0]._finish

    # Call the RequestHandler.finish
    args[0].finish()


# Cache Decorator
def memoize(method):

    @wraps(method)
    def wrapper(*args, **kwargs):

        # Our module wide local_cache
        global local_cache

        if not hasattr(args[0], 'write'):
            raise AttributeError("Could not find the ")

        # Get the class name for the key
        key = repr(args[0])

        # Add the arguments to the key
        for value in args[1:]:
            key += ':%s' % str(value)

        debug('memoize: %s' % key)

        # See if the key is in cache and if so, send it
        if key in local_cache:
            debug('memoize hit: %s' % key)
            return self.finish(local_cache[key])

        # Assign our key
        args[0].tinman_memoize_key = key

        # Monkey-patch the write and finish functions
        args[0]._write = args[0].write
        args[0]._finish = args[0].finish
        args[0].write = memoize_write
        args[0].finish = memoize_finish

        # Return the value
        return method(*args, **kwargs)

    return wrapper


def flush():
    """
    Flush all of the attributes in the cache
    """
    global local_cache
    local_cache = dict()
