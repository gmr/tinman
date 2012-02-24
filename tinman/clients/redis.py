"""
Redis support through the brukva Tornado Redis client:

https://github.com/evilkost/brukva

"""
__author__ = 'Gavin M. Roy <gmr@myyearbook.com>'
__since__ = "2011-07-02"

import brukva
import logging
from tornado import ioloop


class Redis(object):
    """Redis connection object"""

    def __init__(self, host, port, dbnum, password=None):
        """Create our redis object, connecting to the specified host, port and
        database.

        :param host: Redis host to connect to
        :type host: str
        :param port: Redis port to connect to
        :type port: int
        :param dbnum: Redis database number to connect to
        :type dbnum: int
        :param password: Redis database password
        :type password: str
        """
        self._logger = logging.getLogger(__name__)

        ioloop_ = ioloop.IOLoop.instance()

        self._logger.info('Connecting to Redis (%s:%i:%i)', host, port, dbnum)
        self.client = brukva.Client(host, port, password, dbnum, ioloop_)

        try:
            self.client.connect()
        except brukva.ConnectionError as error:
            self._logger.error('Redis connection error: %s', error)
