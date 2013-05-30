"""
process.py

"""
from tinman import application
import clihelper
import copy
from tornado import httpserver
from tornado import ioloop
import logging
import multiprocessing
import signal
import socket
import ssl
from tornado import version as tornado_version

LOGGER = logging.getLogger(__name__)


class Process(multiprocessing.Process):
    """The process holding the HTTPServer and Application"""

    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}):
        """Create a new instance of Process

        """
        super(Process, self).__init__(group, target, name, args, kwargs)

        # Passed in values
        self.manager = kwargs['manager']
        self.port = kwargs['port']

        # Internal attributes holding instance information
        self.app = None
        self.http_server = None
        self.request_counters = dict()

        # If newrelic is passed, use it
        if self.manager.options.newrelic:
            import newrelic.agent
            newrelic.agent.initialize(self.manager.options.newrelic)

        # Fixup the configuration parameters
        self.config = self.fixup_configuration(self.manager.config)

    def create_application(self):
        """Create and return a new instance of tornado.web.Application

        """
        return application.Application(self.routes, self.port, **self.settings)

    def create_http_server(self):
        """Setup the HTTPServer

        :rtype: tornado.httpserver.HTTPServer

        """
        return self.start_httpserver(self.port, self.http_config)

    def fixup_configuration(self, config):
        """Rewrite the SSL certreqs option if it exists, do this once instead
        # of in each process like we do for imports and other things

        :param dict config: the configuration dictionary

        """
        new_config = copy.deepcopy(config)
        if 'ssl_options' in new_config['HTTPServer']:
            self.fixup_ssl_config(new_config['HTTPServer']['ssl_options'])

        # Set the debug to True if running in the foreground
        if self.manager.debug and not new_config['Application'].get('debug'):
            new_config['Application']['debug'] = True

        # Append the HTTP server ports for cross-process functionality
        new_config['Application']['server_ports'] = \
            new_config['HTTPServer']['ports']

        return new_config

    def fixup_ssl_config(self, config):
        """Check the config to see if SSL configuration options have been passed
        and replace none, option, and required with the correct values in
        the certreqs attribute if it is specified.

        :param dict config: the HTTPServer > ssl_options configuration dict

        """
        if 'cert_reqs' in config:
            requirements = {'none': ssl.CERT_NONE,
                            'optional': ssl.CERT_OPTIONAL,
                            'required': ssl.CERT_REQUIRED}
            config['cert_reqs'] = requirements[config['cert_reqs']]

    @property
    def http_config(self):
        """Return a dictionary of HTTPServer arguments using the default values
        as specified in the HTTPServer class docstrings if no values are
        specified.

        :param dict config: The HTTPServer specific section of the config
        :rtype: dict

        """
        config = self.config['HTTPServer']
        return {'no_keep_alive': config.get('no_keep_alive', False),
                'ssl_options': config.get('ssl_options'),
                'xheaders': config.get('xheaders', False)}

    def on_sigterm(self, signal_unused, frame_unused):
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
        self.config = self.fixup_configuration(self.manager.config)
        clihelper.setup_logging(self.manager.debug)

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
        routes = self.app.prepare_routes(self.routes)
        self.app.handlers = []
        self.app.named_handlers = {}
        self.app.add_handlers(".*$", routes)

        LOGGER.info('Configuration reloaded')

    def run(self):
        """Called when the process has started

        :param int port: The HTTP Server port

        """
        LOGGER.debug('Initializing process')

        # Now in a child process so setup logging for this process
        clihelper.setup_logging(self.manager.debug)

        # Register the signal handlers
        self.setup_signal_handlers()

        # Create the application instance
        self.app = self.create_application()

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
    def routes(self):
        """Return the route list from the configuration.

        :rtype: list

        """
        return self.config['Routes']

    @property
    def settings(self):
        """Return the Application configuration

        :rtype: dict

        """
        return self.config['Application']

    def setup_signal_handlers(self):
        """Called when a child process is spawned to register the signal
        handlers

        """
        LOGGER.debug('Registering signal handlers')
        signal.signal(signal.SIGTERM, self.on_sigterm)
        signal.signal(signal.SIGHUP, self.on_sighup)

    def start_httpserver(self, port, args):
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
