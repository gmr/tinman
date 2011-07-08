"""
Tinman command line interface
"""
__author__ = 'Gavin M. Roy'
__email__ = 'gmr@myyearbook.com'
__since__ = '2011-06-06'

# Tinman imports
from . import application
from . import utils
from . import __version__

# General imports
import logging
import multiprocessing
import optparse
import os
import signal
import socket
import sys
import time

# Tornado imports
from tornado import httpserver
from tornado import ioloop
from tornado import version as tornado_version


class TinmanProcess(object):
    """
    Manages the tinman master process when run from the cli
    """

    def __init__(self):

        # Set a default IOloop to None
        self._ioloop = None

        # Get our logger
        self._logger = logging.getLogger('tinman')

    def _build_connections(self, config):
        """Build and attach our supported connections to our IOLoop and
         application object.

        Full configuration file
        """
        # Build a RabbitMQ connection if it exists
        self._build_rabbitmq_connection(config.get('RabbitMQ'))

        # Build a Redis connection if it exists
        self._build_redis_connection(config.get('Redis'))

    def _build_rabbitmq_connection(self, config):
        """Create a connection to RabbitMQ if we have it configured in our
        configuration file.

        :param config: RabbitMQ node of the configuration file dictionary
        :type config: dict
        """
        if not config:
            return

        # Import RabbitMQ only if we need it
        from clients import rabbitmq

        # Create our RabbitMQ instance, it will auto-connect and setup based on
        # this
        rabbitmq = rabbitmq.RabbitMQ(config.get('host'),
                                     config.get('port'),
                                     config.get('virtual_host'),
                                     config.get('username'),
                                     config.get('password'))

        # Add it to our tinman attribute at the application scope
        self._application.tinman.add('rabbitmq', rabbitmq)

    def _build_redis_connection(self, config):
        """Create a connection to Redis if we have it configured in our
        configuration file.

        :param config: Redis node of the configuration file dictionary
        :type config: dict
        """
        if not config:
            return

        # Import Redis only if we need it
        from clients import redis

        # Create our Redis instance, it will auto-connect and setup
        redis = redis.Redis(config.get('host'),
                            config.get('port'),
                            config.get('db'),
                            config.get('password'))

        # Add it to our tinman attribute at the application scope
        self._application.tinman.add('redis', redis)


    def _check_required_configuration_parameters(self, config, options):
        """Validates that the required configuration parameters are set.

        :raises: AttributeError

        """
        # Required sections
        if 'Application' not in config:
            raise AttributeError("Missing Application section in configuration")

        if 'HTTPServer' not in config:
            raise AttributeError("Missing HTTPServer section in configuration")

        if 'Logging' not in config:
            raise AttributeError("Missing Logging section in configuration")

        if not options.route_decorator and 'Routes' not in config:
            raise AttributeError("Missing Routes section in configuration")

        if not options.route_decorator and \
           not isinstance(config['Routes'], list):
            raise AttributeError("Error in Routes section in configuration")

    def _process_options(self):
        """Process the cli options returning the options and arguments"""
        usage = "usage: %prog -c <configfile> [options]"
        version_string = "%%prog v%s" % __version__
        description = "Tinman's Tornado application runner"

        # Create our parser and setup our command line options
        parser = optparse.OptionParser(usage=usage,
                                       version=version_string,
                                       description=description)

        parser.add_option("-c", "--config",
                          action="store",
                          dest="config",
                          help="Specify the configuration file for use")
        parser.add_option("-f", "--foreground",
                          action="store_true",
                          dest="foreground",
                          default=False,
                          help="Run interactively in console")
        parser.add_option("-r", "--route-decorator",
                          action="store_true",
                          dest="route_decorator",
                          default=False,
                          help="Utilize the route decorator instead of the Routes\
                                section of the config")

        # Parse our options and arguments
        return parser.parse_args()

    def _shutdown_signal_handler(self, signum, frame):
        """
        Called on SIGTERM to shutdown the sub-process
        """
        if self._ioloop:
            self._ioloop.stop()

    def _start_processes(self, config):

        # Loop through and kick off our processes
        self._children = []
        for port in config['HTTPServer']['ports']:
            self._logger.info("Starting Tinman v%s process for port %i",
                              __version__, port)
            # Kick off the child process
            child = multiprocessing.Process(target=self._start_server,
                                            name="tinman-%i" % port,
                                            args=(config, port))
            self._children.append(child)
            child.start()

        # Log our completion
        self._logger.debug("All children spawned")

    def _start_server(self, config, port):

        # Setup our signal handler
        signal.signal(signal.SIGTERM, self._shutdown_signal_handler)

        # Start our application
        self._application = \
            application.TinmanApplication(config.get('Routes', None),
                                          **config.get('Application', dict()))

        # Try and build any connection types we automatically support
        self._build_connections(config)

        # Start the HTTP Server
        self._logger.info("Starting Tornado v%s HTTPServer on port %i",
                          tornado_version, port)
        http_server = httpserver.HTTPServer(self._application)
        try:
            http_server.listen(port)
        except socket.error as error:
            # If we couldn't bind to IPv6 (Tornado 2.0+)
            if str(error).find('bad family'):
                http_server.bind(port, family=socket.AF_INET)
                http_server.start(1)

        # Get a handle to the instance of IOLoop
        self._ioloop = ioloop.IOLoop.instance()

        # Start the IOLoop
        try:
            self._ioloop.start()
        except KeyboardInterrupt:
            self._logger.info('KeyboardInterrupt received, shutting down.')

    def run(self):
        """Run the Tinman Process"""

        # Process our command line options
        options, args = self._process_options()

        # No configuration file?
        if options.config is None:
            sys.stdout.write("\nConfiguration not specified, \
running Tinman Test Application\n")
            from . import test
            config = test.CONFIG

        # Load the configuration file
        else:
            config = utils.load_configuration_file(options.config)

        # Check our required options
        self._check_required_configuration_parameters(config, options)

        # If we have a base path set prepend it to our Python import path
        if 'base_path' in config:
            sys.path.insert(0, config['base_path'])

        # Setup our logging
        utils.setup_logging(config['Logging'], options.foreground)

        # Setup our signal handlers
        utils.setup_signals()

        # Daemonize if we need to
        if not options.foreground:
            utils.daemonize(pidfile=config.get("pidfile", None),
                            user=config.get("user", None),
                            group=config.get("group", None))
        else:
            config['Application']['debug'] = True

        self._start_processes(config)

        # Have a main event loop for dealing with stats
        utils.running = True
        while utils.running:
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                self._logger.info("CTRL-C pressed, shutting down.")
                break

        # Tell all the children to shutdown
        for child in self._children:
            self._logger.debug("Sending terminate signal to %s", child.name)
            child.terminate()

        # Loop while the children are shutting down
        self._logger.debug("Waiting for children to shutdown")
        while True in [child.is_alive() for child in self._children]:
            time.sleep(0.5)

        # Remove our pidfile
        if 'pidfile' in config:
            if os.path.exists(config['pidfile']):
                try:
                    os.unlink(config['pidfile'])
                except OSError as e:
                    self._logger.error("Could not remove pidfile: %s", e)

        # Log that we're shutdown cleanly
        self._logger.info("tinman has shutdown")
