"""
process.py

"""
from helper import config as helper_config
from tornado import httpserver
from tornado import ioloop
import logging
import multiprocessing
import signal
import socket
import ssl
from tornado import version as tornado_version

from tinman import application
from tinman import config
from tinman import exceptions

LOGGER = logging.getLogger(__name__)


class Process(multiprocessing.Process):
    """The process holding the HTTPServer and Application"""
    CERT_REQUIREMENTS = {config.NONE: ssl.CERT_NONE,
                         config.OPTIONAL: ssl.CERT_OPTIONAL,
                         config.REQUIRED: ssl.CERT_REQUIRED}
    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}):
        """Create a new instance of Process

        """
        super(Process, self).__init__(group, target, name, args, kwargs)

        # Passed in values
        self.namespace = kwargs['namespace']
        self.port = kwargs['port']

        # Internal attributes holding instance information
        self.app = None
        self.http_server = None
        self.request_counters = dict()

        # Re-setup logging in the new process
        self.logging_config = None

        # If newrelic is passed, use it
        if self.newrelic_ini_path:
            self.setup_newrelic()

    def create_application(self):
        """Create and return a new instance of tinman.application.Application"""
        return application.Application(self.settings,
                                       self.namespace.routes,
                                       self.port)

    def create_http_server(self):
        """Setup the HTTPServer

        :rtype: tornado.httpserver.HTTPServer

        """
        return self.start_http_server(self.port, self.http_config)

    @property
    def http_config(self):
        """Return a dictionary of HTTPServer arguments using the default values
        as specified in the HTTPServer class docstrings if no values are
        specified.

        :param dict config: The HTTPServer specific section of the config
        :rtype: dict

        """
        return {config.NO_KEEP_ALIVE:
                    self.namespace.server.get(config.NO_KEEP_ALIVE, False),
                config.SSL_OPTIONS: self.ssl_options,
                config.XHEADERS: self.namespace.server.get(config.XHEADERS,
                                                           False)}

    def on_sigabrt(self, signal_unused, frame_unused):
        """Stop the HTTP Server and IO Loop, shutting down the process

        :param int signal_unused: Unused signal number
        :param frame frame_unused: Unused frame the signal was caught in

        """
        LOGGER.info('Stopping HTTP Server and IOLoop')
        self.http_server.stop()
        self.ioloop.stop()

    def on_sighup(self, signal_unused, frame_unused):
        """Reload the configuration

        :param int signal_unused: Unused signal number
        :param frame frame_unused: Unused frame the signal was caught in

        """
        # Update HTTP configuration
        for setting in self.http_config:
            if getattr(self.http_server, setting) != self.http_config[setting]:
                LOGGER.debug('Changing HTTPServer %s setting', setting)
                setattr(self.http_server, setting, self.http_config[setting])

        # Update Application Settings
        for setting in self.settings:
            if self.app.settings[setting] != self.settings[setting]:
                LOGGER.debug('Changing Application %s setting', setting)
                self.app.settings[setting] = self.settings[setting]

        # Update the routes
        self.app.handlers = []
        self.app.named_handlers = {}
        routes = self.namespace.config.get(config.ROUTES)
        self.app.add_handlers(".*$", self.app.prepare_routes(routes))

        LOGGER.info('Configuration reloaded')

    def run(self):
        """Called when the process has started

        :param int port: The HTTP Server port

        """
        LOGGER.debug('Initializing process')

        # Setup logging
        self.logging_config = self.setup_logging()

        # Register the signal handlers
        self.setup_signal_handlers()

        # Create the application instance
        try:
            self.app = self.create_application()
        except exceptions.NoRoutesException:
            return

        # Create the HTTPServer
        self.http_server = self.create_http_server()

        # Hold on to the IOLoop in case it's needed for responding to signals
        self.ioloop = ioloop.IOLoop.instance()

        # Start the IOLoop, blocking until it is stopped
        try:
            self.ioloop.start()
        except KeyboardInterrupt:
            pass

    @property
    def settings(self):
        """Return the Application configuration

        :rtype: dict

        """
        return dict(self.namespace.config)

    def setup_logging(self):
        return helper_config.LoggingConfig(self.namespace.logging)

    @property
    def newrelic_ini_path(self):
        return self.namespace.config.get(config.NEWRELIC)

    def setup_newrelic(self):
        """Setup the NewRelic python agent"""
        import newrelic.agent
        newrelic.agent.initialize(self.newrelic_ini_path)

    def setup_signal_handlers(self):
        """Called when a child process is spawned to register the signal
        handlers

        """
        LOGGER.debug('Registering signal handlers')
        signal.signal(signal.SIGABRT, self.on_sigabrt)

    @property
    def ssl_options(self):
        """Check the config to see if SSL configuration options have been passed
        and replace none, option, and required with the correct values in
        the certreqs attribute if it is specified.

        :rtype: dict

        """
        opts = self.namespace.server.get(config.SSL_OPTIONS) or dict()
        if config.CERT_REQS in opts:
            opts[config.CERT_REQS] = \
                self.CERT_REQUIREMENTS[opts[config.CERT_REQS]]
        return opts or None

    def start_http_server(self, port, args):
        """Start the HTTPServer

        :param int port: The port to run the HTTPServer on
        :param dict args: Dictionary of arguments for HTTPServer
        :rtype: tornado.httpserver.HTTPServer

        """
        # Start the HTTP Server
        LOGGER.info("Starting Tornado v%s HTTPServer on port %i Args: %r",
                    tornado_version, port, args)
        http_server = httpserver.HTTPServer(self.app, **args)
        http_server.bind(port, family=socket.AF_INET)
        http_server.start(1)
        return http_server
