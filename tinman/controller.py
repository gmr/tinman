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

LOGGER = logging.getLogger(__name__)


class Controller(helper.Controller):
    """Tinman controller is the core application coordinator, responsible for
    spawning and managing children.

    """
    DEFAULT_PORTS = [8900]
    MAX_SHUTDOWN_WAIT = 4

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

        if hasattr(self.config.application, config.PATHS):
            if hasattr(self.config.application.paths, config.BASE):
                sys.path.insert(0, self.config.application.paths.base)

    @property
    def living_children(self):
        """Returns a list of all child processes that are still alive.

        :rtype: list

        """
        return [child for child in self.children if child.is_alive()]

    def configuration_reloaded(self):
        """Send a SIGHUP to child processes"""
        LOGGER.info('Notifying children of new configuration updates')
        self.signal_children(signal.SIGHUP)

    def process(self):
        """Check up on child processes and make sure everything is running as
        it should be.

        """
        LOGGER.debug('%i active children', len(self.living_children))

    @property
    def ports_to_spawn(self):
        """Return the list of ports to spawn

        :rtype: list

        """
        return (self.config.get(config.HTTP_SERVER, dict()).get(config.PORTS)
                or self.DEFAULT_PORTS)

    def set_base_path(self, value):
        """Munge in the base path into the configuration values

        :param str value: The path value

        """
        if config.PATHS not in self.config.application:
            self.config.application[config.PATHS] = dict()

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
        self.namespace.args = self.args
        self.namespace.config = dict(self.config.application)
        self.namespace.logging = self.config.logging
        self.namespace.debug = self.debug
        self.namespace.routes = self.config.get(config.ROUTES)
        self.namespace.server = self.config.get(config.HTTP_SERVER)
        self.spawn_processes()

    def shutdown(self):
        """Send SIGABRT to child processes to instruct them to stop"""
        self.signal_children(signal.SIGABRT)

        # Wait a few iterations when trying to stop children before terminating
        waiting = 0
        while self.living_children:
            time.sleep(0.5)
            waiting += 1
            if waiting == self.MAX_SHUTDOWN_WAIT:
                self.signal_children(signal.SIGKILL)
                break

    def signal_children(self, signum):
        """Send a signal to all children

        :param int signum: The signal to send

        """
        LOGGER.info('Sending signal %i to children', signum)
        for child in self.living_children:
            if child.pid != os.getpid():
                os.kill(child.pid, signum)

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
        for port in self.ports_to_spawn:
            process = self.spawn_process(port)
            process.start()
            self.children.append(process)


def main():
    """Invoked by the script installed by setuptools."""
    parser.name('tinman')
    parser.description(__desc__)

    p = parser.get()
    p.add_argument('-p', '--path',
                   action='store_true',
                   dest='path',
                   help='Path to prepend to the Python system path')

    helper.start(Controller)
