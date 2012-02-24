"""
Tinman command line interface
"""
__author__ = 'Gavin M. Roy'
__email__ = 'gmr@myyearbook.com'
__since__ = '2011-06-06'

# Tinman imports
from . import application
from . import __version__

# General imports
import logging
import logging_config
import multiprocessing
import signal
import socket

# Tornado imports
from tornado import httpserver
from tornado import ioloop
from tornado import version as tornado_version


class TinmanProcess(object):
    """
    Manages the tinman master process when run from the cli
    """
    def __init__(self, config):
        """Create a TinmanProcess object

        :param dict config: The configuration dictionary

        """
        # Set a default IOloop to None
        self._ioloop = None

        # Set the configuration
        self._config = config

        # Get our logger
        self._logger = logging.getLogger(__name__)

        # Setup logging
        self._setup_logging(config['Logging'],
                            config['Application'].get('debug', False))

    def _build_connections(self):
        """Build and attach our supported connections to our IOLoop and
         application object.

        """
        # Build a PostgreSQL connection if it exists
        if self._config.get('Postgres'):
            self._build_postgres_connection()

        # Build a RabbitMQ connection if it exists
        if self._config.get('RabbitMQ'):
            self._build_rabbitmq_connection()

        # Build a Redis connection if it exists
        if self._config.get('Redis'):
            self._build_redis_connection()

    def _build_postgres_connection(self):
        """Create a connection to PostgreSQL if we have it configured in our
        configuration file.

        """
        # Import Redis only if we need it
        from clients import pgsql

        # Get a Redis specific config node
        config = self._config['Postgres']

        # Create our Redis instance, it will auto-connect and setup
        conn = pgsql.PgSQL(config.get('host'),
                           config.get('port'),
                           config.get('dbname'),
                           config.get('user'),
                           config.get('password'))

        # Add it to our tinman attribute at the application scope
        self._app.tinman.add('pgsql', conn)

    def _build_rabbitmq_connection(self):
        """Create a connection to RabbitMQ if we have it configured in our
        configuration file.

        """
        # Import RabbitMQ only if we need it
        from clients import rabbitmq

        # Get a RabbitMQ specific config node
        config = self._config['RabbitMQ']

        # Create our RabbitMQ instance, it will auto-connect and setup based on
        # this
        rabbitmq = rabbitmq.RabbitMQ(config.get('host'),
                                     config.get('port'),
                                     config.get('virtual_host'),
                                     config.get('username'),
                                     config.get('password'))

        # Add it to our tinman attribute at the application scope
        self._app.tinman.add('rabbitmq', rabbitmq)

    def _build_redis_connection(self):
        """Create a connection to Redis if we have it configured in our
        configuration file.

        """
        # Import Redis only if we need it
        from clients import redis

        # Get a Redis specific config node
        config = self._config['Redis']

        # Create our Redis instance, it will auto-connect and setup
        redis = redis.Redis(config.get('host'),
                            config.get('port'),
                            config.get('db'),
                            config.get('password'))

        # Add it to our tinman attribute at the application scope
        self._app.tinman.add('redis', redis)

    def _shutdown_signal_handler(self, signum, frame):
        """Called on SIGTERM to shutdown the sub-process"""
        if self._ioloop:
            self._ioloop.stop()

    @property
    def _http_server_arguments(self):
        """Return a dictionary of HTTPServer arguments using the default values
        as specified in the HTTPServer class docstrings if no values are
        specified.

        :returns: dict

        """
        # No reason to not always pass these
        args = {'no_keep_alive': self._config['HTTPServer'].get('no_keep_alive',
                                                                  False),
                'xheaders': self._config['HTTPServer'].get('xheaders',
                                                           False)}

        # Only pass ssl_options if we have it set in the config
        if 'ssl_options' in self._config['HTTPServer']:
            args['ssl_options'] = self._config['HTTPServer'].get('ssl_options',
                                                                 dict())
        # Return the arguments
        return args

    def _setup_logging(self, config, debug):
        """Construct the logging config object and

        """
        self._logging = logging_config.Logging(config, debug)
        self._logging.setup()

    def _start_httpserver(self, port, args):
        """Start the HTTPServer

        :param int port: The port to run the HTTPServer on
        :param dict args: Dictionary of arguments for HTTPServer

        """
        # Start the HTTP Server
        self._logger.info("Starting Tornado v%s HTTPServer on port %i",
                          tornado_version, port)
        http_server = httpserver.HTTPServer(self._app, **args)
        try:
            http_server.listen(port)
        except socket.error as error:
            # If we couldn't bind to IPv6 (Tornado 2.0+)
            if str(error).find('bad family'):
                http_server.bind(port, family=socket.AF_INET)
                http_server.start(1)

        # Patch in the HTTP Port for Logging
        self._app.http_port = port

    def _subprocess_start(self, config, port):
        """Start the process specific application and HTTP server for the given
        config and port

        :param dict config: The configuration dictionary parsed by Tinman
        :param int port: The port to listen on

        """
        # Setup our signal handler
        signal.signal(signal.SIGTERM, self._shutdown_signal_handler)

        # Start our application
        self._app = application.TinmanApplication(config.get('Routes', None),
                                                  **config.get('Application',
                                                               dict()))

        # Try and build any connection types we automatically support
        self._build_connections()

        # Build a dictionary of valid HTTP Server arguments
        args = self._http_server_arguments

        # Start the HTTP Server
        self._start_httpserver(port, args)

        # Get a handle to the instance of IOLoop
        self._ioloop = ioloop.IOLoop.instance()

        # Start the IOLoop
        try:
            self._ioloop.start()
        except KeyboardInterrupt:
            self._logger.info('KeyboardInterrupt received, shutting down.')

    def start(self, config):
        """Start the TinmanProcess for the given config. This will in turn
        spawn a new process for each port of the HTTP server and then move on.

        :param dict config: The configuration dictionary parsed by Tinman

        """
        # Loop through and kick off our processes
        self._children = []
        for port in config['HTTPServer']['ports']:
            self._logger.info("Starting Tinman v%s process for port %i",
                              __version__, port)

            # Kick off the child process
            child = multiprocessing.Process(target=self._subprocess_start,
                                            name="tinman-%i" % port,
                                            args=(config, port))
            self._children.append(child)
            child.start()

        # Log our completion
        self._logger.debug("%i child(ren) spawned", len(self._children))
