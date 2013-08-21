"""The Tinman Controller class, uses clihelper for most of the main
functionality with regard to configuration, logging and daemoniaztion. Spawns a
tornado.HTTPServer and Application per port using multiprocessing.

"""
import helper
import logging
from helper import parser
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

# Default port
DEFAULT_PORT = 8900

# Process count defaults to the number of CPUs if not configured
DEFAULT_PROCESS_COUNT = multiprocessing.cpu_count()

LOGGER = logging.getLogger(__name__)


class Controller(helper.Controller):
    """Tinman controller is the core application coordinator, responsible for
    spawning and managing children.

    """
    def enable_debug(self):
        """If the cli arg for foreground is set, set the configuration option
        for debug.

        """
        if self.args.foreground:
            self.config.application[config.DEBUG] = True

    def insert_paths(self):
        """Inserts a base path into the sys.path list if one is specified in
        the configuration.

        """
        if self.args.path:
            sys.path.insert(0, self.args.path)
        if self.config.application.get(config.BASE, dict()).get(config.PATHS):
            sys.path.insert(0,
                            self.config.application[config.BASE][config.PATHS])

    @property
    def living_children(self):
        return [child for child in self.children if child.is_alive()]

    @property
    def process_count_to_spawn(self):
        """Return the number of processes to spawn, sending a single process
        if in debug mode, otherwise the configured value defaulting to
        DEFAULT_PROCESS_COUNT if not set.

        :rtype: int

        """
        if self.debug:
            return 1
        return self.config.application.server.processes or DEFAULT_PROCESS_COUNT

    def set_base_path(self, value):
        """Munge in the base path into the configuration values

        :param str value: The path value

        """
        if config.PATHS not in self.config.application:
            print config.PATHS
            self.config.application[config.PATHS] = dict()
            print self.config.application

        if config.BASE not in self.config.application[config.PATHS]:
            self.config.application[config.PATHS][config.BASE] = value

    def setup(self):
        """Additional setup steps."""
        LOGGER.info('Tinman v%s starting up with Tornado v%s',
                    __version__, tornado_version)
        # Setup debugging and paths
        self.enable_debug()
        self.set_base_path(os.getcwd())
        self.insert_paths()

        # Setup child processes
        self.children = list()
        self.manager = multiprocessing.Manager()
        self.namespace = self.manager.Namespace()
        self.namespace.config = dict(self.config.application)
        self.namespace.debug = self.debug
        self.namespace.args = self.args
        self.spawn_processes()

    def spawn_process(self, port):
        """Create an Application and HTTPServer for the given port.

        :param int port: The port to listen on
        :rtype: multiprocessing.Process

        """
        return process.Process(name="ServerProcess.%i" % port,
                               kwargs={'namespace': self.namespace,
                                       'port': port})

    def spawn_processes(self):
        """Spawn of the appropriate number of application processes"""
        port = self.config.application.get(config.HTTP_SERVER,
                                           dict()).get(config.HTTP_PORT,
                                                       DEFAULT_PORT)
        processes = self.process_count_to_spawn
        LOGGER.info('Spawning %i applicatication processes on port %i',
                    processes, port)
        for number in range(0, self.process_count_to_spawn):
            process = self.spawn_process(port)
            process.start()
            self.children.append(process)


def main():
    """Invoked by the script installed by setuptools."""
    parser.name('tinman')
    parser.description(__desc__)

    p = parser.get()
    p.add_argument('-n', '--newrelic',
                   action='store',
                   dest='newrelic',
                   help='Path to newrelic.init for enabling NewRelic '
                        'instrumentation')
    p.add_argument('-p', '--path',
                   action='store_true',
                   dest='path',
                   help='Path to prepend to the Python system path')

    helper.start(Controller)
