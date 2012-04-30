"""
process.py

"""

__author__ = 'Gavin M. Roy'
__email__ = 'gmr@myyearbook.com'
__since__ = '2012-04-29'

from tinman import application
import clihelper
from tornado import httpserver
from tornado import ioloop
import logging
import multiprocessing
import signal
import socket
import ssl
from tornado import version as tornado_version

logger = logging.getLogger(__name__)


class TinmanProcess(multiprocessing.Process):
    """The process holding the HTTPServer and Application"""

    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}):
        """Create a new instance of TinmanProcess

        """
        super(TinmanProcess, self).__init__(group, target, name, args, kwargs)

        # Passed in values
        self._config = args[0]
        self._port = args[1]
        self._stats_queue = args[2]
        self._debug = args[3]

        # Internal attributes holding instance information
        self._app = None
        self._server = None
        self._request_counters = dict()

        # Fixup the configuration parameters
        self._fixup_configuration(self._config)

    def _application(self, config):
        """Create and return a new instance of tornado.web.Application

        :param dict config: The application configuration

        """
        logging.debug('Creating a new Application with %r', config)
        return application.TinmanApplication(self._get_routes(), **config)

    def _fixup_configuration(self, config):
        """Rewrite the SSL certreqs option if it exists, do this once instead
        # of in each process like we do for imports and other things

        :param dict config: the configuration dictionary

        """
        if 'ssl_options' in config['HTTPServer']:
            self._fixup_ssl_config(config['HTTPServer']['ssl_options'])

        # Set the debug to True if running in the foreground
        if self._debug and not config['Application'].get('debug'):
            config['Application']['debug'] = True

    def _fixup_ssl_config(self, config):
        """Check the config to see if SSL configuration options have been passed
        and replace none, option, and required with the correct values in
        the certreqs attribute if it is specified.

        :param dict config: the HTTPServer > ssl_options configuration dict

        """
        if 'cert_reqs' in config:

            # Build a mapping dictionary
            requirements = {'none': ssl.CERT_NONE,
                            'optional': ssl.CERT_OPTIONAL,
                            'required': ssl.CERT_REQUIRED}
            # Remap the value
            config['cert_reqs'] = requirements[config['cert_reqs']]

    def _get_application_config(self):
        """Return the Application configuration

        :rtype: dict

        """
        return self._config['Application']

    def _get_handlers(self):
        """Return the dictionary of URI to Handler mappings, providing
        instances of the handlers instead of the classes.

        :rtype: dict

        """
        routes = self._get_routes_config()



    def _get_http_server_config(self):
        """Return the HTTPServer configuration

        :rtype: dict

        """
        return self._config['HTTPServer']

    def _get_postgres_config(self):
        """Return the PostgreSQL configuration if it exists

        :rtype: dict

        """
        return self._config.get('PostgreSQL')

    def _get_rabbitmq_config(self):
        """Return the RabbitMQ configuration if it exists

        :rtype: dict

        """
        return self._config.get('RabbitMQ')

    def _get_redis_config(self):
        """Return the RabbitMQ configuration if it exists

        :rtype: dict

        """
        return self._config.get('RabbitMQ')

    def _get_routes(self):
        """Return the route list from the configuration.

        :rtype: list

        """
        return self._config['Routes']

    def _http_server(self, config):
        """Setup the HTTPServer

        :rtype: tornado.httpserver.HTTPServer

        """
        logger.debug('Returning a HTTPServer with %r', config)
        return self._start_httpserver(self._port,
                                      self._http_server_arguments(config))

    def _http_server_arguments(self, config):
        """Return a dictionary of HTTPServer arguments using the default values
        as specified in the HTTPServer class docstrings if no values are
        specified.

        :param dict config: The HTTPServer specific section of the config
        :rtype: dict

        """
        return {'no_keep_alive': config.get('no_keep_alive', False),
                'ssl_options': config.get('ssl_options'),
                'xheaders': config.get('xheaders', False)}

    def _setup_services(self):
        """Create an instance for each of the configured auto-configured
        services.

        """


    def _setup_signal_handlers(self):
        """Called when a child process is spawned to register the signal
        handlers

        """
        logger.debug('Registering signal handlers')
        signal.signal(signal.SIGTERM, self.on_sigterm)

    def _setup_postgresql(self):
        """If a PostgreSQL instance is configured, create a new PostgreSQL
        connection and cursor.

        """
        config = self._get_postgres_config()
        if not config:
            return None

        logger.debug('Constructing PostgreSQL Connection')
        from tinman.clients import pgsql

        return pgsql.PgSQL(config.get('host'),
                           config.get('port'),
                           config.get('dbname'),
                           config.get('user'),
                           config.get('password'))

    def _setup_rabbitmq_connection(self):
        """Create a connection to RabbitMQ if we have it configured in our
        configuration file.

        """
        config = self._get_redis_config()
        if not config:
            return None

        # Import RabbitMQ only if we need it
        from clients import rabbitmq

        # Create the connected RabbitMQ instance
        return rabbitmq.RabbitMQ(config.get('host'),
                                 config.get('port'),
                                 config.get('virtual_host'),
                                 config.get('username'),
                                 config.get('password'))

    def _setup_redis_connection(self):
        """Create a connection to Redis if we have it configured in our
        configuration file.

        """
        config = self._get_redis_config()
        if not config:
            return None

        # Import Redis only if we need it
        from clients import redis

        # Create our Redis instance, it will auto-connect and setup
        return redis.Redis(config.get('host'),
                           config.get('port'),
                           config.get('db'),
                           config.get('password'))

    def _start_httpserver(self, port, args):
        """Start the HTTPServer

        :param int port: The port to run the HTTPServer on
        :param dict args: Dictionary of arguments for HTTPServer
        :rtype: tornado.httpserver.HTTPServer

        """
        # Start the HTTP Server
        logger.info("Starting Tornado v%s HTTPServer on port %i",
                    tornado_version, port)
        http_server = httpserver.HTTPServer(self._application,
                                            **args)
        try:
            http_server.listen(port)
        except socket.error as error:
            # If we couldn't bind to IPv6 (Tornado 2.0+)
            if str(error).find('bad family'):
                http_server.bind(port, family=socket.AF_INET)
                http_server.start(1)

        # Patch in the HTTP Port for Logging
        self._app.http_port = port

        return http_server

    def on_sigterm(self, signal, frame):
        logger.debug('Child process received SIGTERM')

        # Stop the IOLoop
        self._ioloop.stop()

    def run(self):
        """Called when the process has started

        :param int port: The HTTP Server port

        """
        logger.debug('Initializing process')

        # Now in a child process so setup logging for this process
        clihelper.setup_logging(self._debug)

        # Register the signal handlers
        self._setup_signal_handlers()

        # Create the application instance
        self._app = self._application(self._get_application_config())

        # Setup the auto-created IO services
        self._setup_services()

        # Create the HTTPServer
        self._server = self._http_server(self._get_http_server_config())

        # Hold on to the IOLoop in case it's needed for responding to signals
        self._ioloop = ioloop.IOLoop.instance()

        # Start the IOLoop, blocking until it is stopped
        try:
            self._ioloop.start()
        except KeyboardInterrupt:
            pass
