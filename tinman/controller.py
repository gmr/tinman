"""
The Tinman Controller class, uses clihelper for most of the main functionality
with regard to configuration, logging and daemoniaztion. Spawns a
tornado.HTTPServer and Application per port using multiprocessing.

"""
import clihelper
import logging
import multiprocessing
import sys
import time
from tornado import version as tornado_version


# Tinman Imports
from tinman import __desc__
from tinman import __version__
from tinman import config
from tinman import process

# Additional required configuration keys
_REQUIRED_CONFIG_KEYS = [config.HTTP_SERVER, config.ROUTES]
_SHUTDOWN_SLEEP_INTERVAL = 0.25

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
        self._children = list()
        self._stats_queue = self._create_stats_queue()

    @property
    def http_server_config(self):
        """Return the HTTPServer configuration

        :rtype: dict

        """
        return self._config[config.HTTP_SERVER]

    def _create_process(self, port):
        """Create an Application and HTTPServer for the given port.

        :param int port: The port to listen on
        :rtype: multiprocessing.Process

        """
        LOGGER.info('Creating process for TCP port %i', port)
        return process.Process(name="ServerProcess.%i" % port,
                               args=(self._config,
                                     port,
                                     self._stats_queue,
                                     self._debug))

    def _create_stats_queue(self):
        """Return an instance of multiprocessing.Queue for passing stats back
        to this process.

        :rtype: multiprocessing.Queue

        """
        return multiprocessing.Queue()

    def _insert_path(self, path):
        """Insert a path into the Python system paths.

        """
        sys.path.insert(0, path)

    @property
    def _config_base_path(self):
        return self.application_config.get(config.PATHS,
                                           dict()).get(config.BASE)

    def _set_base_path(self, value):
        if config.PATHS not in self._config[config.APPLICATION]:
            self._config[config.APPLICATION][config.PATHS] = dict()
        self._config[config.APPLICATION][config.PATHS][config.BASE] = value

    def _insert_base_path(self):
        """Inserts a base path into the sys.path list if one is specified in
        the configuration.

        """
        if hasattr(self._options, 'path') and self._options.path:
            self._set_base_path(self._options.path)
        if self._config_base_path:
            LOGGER.debug('Appending %s to the sys.path list',
                         self._config_base_path)
            self._insert_path(self._config_base_path)

    def _process(self):
        """Called when the controlling loop wakes. Use to gather stats
        information to present to the stats HTTP server.

        """
        LOGGER.debug('Waking up parent process')

    def _reload_configuration(self):
        """Reload the configuration via clihelper.Controller and then perform
        the fixups needed.

        """
        super(Controller, self).reload_configuration()

        # Notify children

    def _setup(self):
        """Additional setup steps."""
        LOGGER.info('Tinman v%s starting up with Tornado v%s',
                    __version__, tornado_version)
        self._insert_base_path()
        self._start_children()

    def _shutdown(self):
        """Called when the application is shutting down, notify the child
        processes and loop until they are shutdown.

        """
        self.set_state(self.STATE_STOPPING)

        LOGGER.info('Terminating child processes')
        for child in self._children:
            child.terminate()

        # Loop while children are alive
        LOGGER.info('Waiting for all child processes to die')
        while all([child.is_alive() for child in self._children]):
            time.sleep(_SHUTDOWN_SLEEP_INTERVAL)

        LOGGER.debug('All child processes have stopped')

        # Note that the shutdown process is complete
        self._stopped()

    def _start_children(self):
        """Start the child processes"""
        for port in self.http_server_config['ports']:
            child = self._create_process(port)
            child.start()
            self._children.append(child)


def add_required_config_keys():
    """Add each of the items in the _REQUIRED_CONFIG_KEYS to the
    clihelper._CONFIG_KEYS for validation of the configuration file. If one of
    the items is not present in the config file, an exception will be thrown
    and the application will be shutdown.

    """
    [clihelper.add_config_key(key) for key in _REQUIRED_CONFIG_KEYS]


def setup_options(parser):
    """Called by the clihelper._cli_options method if passed to the
    Controller.run method.

    """
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
