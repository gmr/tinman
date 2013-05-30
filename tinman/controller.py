"""The Tinman Controller class, uses clihelper for most of the main
functionality with regard to configuration, logging and daemoniaztion. Spawns a
tornado.HTTPServer and Application per port using multiprocessing.

"""
import clihelper
import logging
import multiprocessing
import os
import signal
import sys
import time
from tornado import version as tornado_version


# Tinman Imports
from tinman import __desc__
from tinman import __version__
from tinman import config
from tinman import process

# Additional required configuration keys
REQUIRED_CONFIG_KEYS = [config.HTTP_SERVER, config.ROUTES]
MAX_SHUTDOWN_WAIT = 2
SHUTDOWN_SLEEP_INTERVAL = 0.25


LOGGER = logging.getLogger(__name__)


class Controller(clihelper.Controller):
    """Main application controller class. Responsible for spawning all of the
    HTTPServer / Applications.

    """
    def __init__(self, options, arguments):
        """Create a new instance of the Controller class

        :param optparse.Values options: CLI Options
        :param list arguments: Additional CLI arguments

        """
        super(Controller, self).__init__(options, arguments)
        self.children = list()
        self.manager = multiprocessing.Manager()
        self.manager.child_stats = list()
        self.manager.config = self.config
        self.manager.debug = self._debug
        self.manager.options = options

    @property
    def config_base_path(self):
        return self.application_config.get(config.PATHS,
                                           dict()).get(config.BASE)

    def create_process(self, port):
        """Create an Application and HTTPServer for the given port.

        :param int port: The port to listen on
        :rtype: multiprocessing.Process

        """
        LOGGER.info('Creating HTTPServer and Application on port %i', port)
        return process.Process(name="ServerProcess.%i" % port,
                               kwargs={'manager': self.manager,
                                       'port': port})

    @property
    def http_server_config(self):
        """Return the HTTPServer configuration

        :rtype: dict

        """
        return self._config[config.HTTP_SERVER]

    def insert_base_path(self):
        """Inserts a base path into the sys.path list if one is specified in
        the configuration.

        """
        if hasattr(self._options, 'path') and self._options.path:
            self.set_base_path(self._options.path)
        if self.config_base_path:
            LOGGER.debug('Appending %s to the sys.path list',
                         self.config_base_path)
            self.insert_path(self.config_base_path)

    def insert_path(self, path):
        """Insert a path into the Python system paths.

        """
        sys.path.insert(0, path)

    @property
    def living_children(self):
        return [child for child in self.children if child.is_alive()]

    def set_base_path(self, value):
        """Munge in the base path into the configuration values

        :param str value: The path value

        """
        if config.PATHS not in self._config[config.APPLICATION]:
            self._config[config.APPLICATION][config.PATHS] = dict()
        self._config[config.APPLICATION][config.PATHS][config.BASE] = value

    def reload_configuration(self):
        """Reload the configuration via clihelper.Controller and then notify
        children up the update

        """
        super(Controller, self).reload_configuration()
        for child in self.living_children:
            if child.pid != os.getpid():
                os.kill(child.pid, signal.SIGHUP)

    def setup(self):
        """Additional setup steps."""
        LOGGER.info('Tinman v%s starting up with Tornado v%s',
                    __version__, tornado_version)
        self.insert_base_path()
        self.start_children()

    def start_children(self):
        """Start the child processes"""
        for port in self.http_server_config['ports']:
            child = self.create_process(port)
            child.start()
            self.children.append(child)

    def stop(self):
        """Called when the application is shutting down, notify the child
        processes and loop until they are shutdown.

        """
        self.set_state(self.STATE_STOPPING)

        # Signal Children to Stop
        LOGGER.info('Stopping child processes')
        for child in self.living_children:
            child.terminate()

        # Loop while children are alive
        LOGGER.info('Waiting for all child processes to die')
        start_time = time.time()
        while self.living_children:
            time.sleep(SHUTDOWN_SLEEP_INTERVAL)
            if time.time() - start_time >= MAX_SHUTDOWN_WAIT:
                LOGGER.info('All children did not stop in time')
                break

        if self.living_children:
            LOGGER.info('Killing child processes')
            for child in self.living_children:
                if child.pid != os.getpid():
                    os.kill(child.pid, signal.SIGKILL)

        # Note that the shutdown process is complete
        self._stopped()


def add_required_config_keys():
    """Add each of the items in the _REQUIRED_CONFIG_KEYS to the
    clihelper._CONFIG_KEYS for validation of the configuration file. If one of
    the items is not present in the config file, an exception will be thrown
    and the application will be shutdown.

    """
    [clihelper.add_config_key(key) for key in REQUIRED_CONFIG_KEYS]


def setup_options(parser):
    """Called by the clihelper._cli_options method if passed to the
    Controller.run method.

    """
    parser.add_option("-n", "--newrelic",
                      action="store",
                      dest="newrelic",
                      default=None,
                      help="Path to newrelic.ini to enable NewRelic "
                           "instrumentation")
    parser.add_option("-p", "--path",
                      action="store",
                      dest="path",
                      default=None,
                      help="Path to prepend to the Python system path")


def main():
    """Invoked by the script installed by setuptools."""
    clihelper.setup('tinman', __desc__, __version__)
    add_required_config_keys()
    clihelper.run(Controller, setup_options)
