"""
Wrap the command line interaction in an object

"""
__author__ = 'Gavin M. Roy'
__email__ = 'gmr@myyearbook.com'
__since__ = '2011-12-31'

# Tinman imports
from . import process
from . import utils
from . import __version__

import logging
import optparse
import os
import sys
import time


class TinmanCLI(object):
    """Main application controller class"""
    def __init__(self):
        """Create a new instance of the TinmanCLI class"""
        self._children = list()
        self._config = None
        self._options = None
        self._logger = logging.getLogger('tinman.cli')

    def _check_required_configuration_parameters(self):
        """Validates that the required configuration parameters are set.

        :raises: AttributeError

        """
        # Required sections
        if 'Application' not in self._config:
            raise AttributeError("Missing Application section in configuration")

        if 'HTTPServer' not in self._config:
            raise AttributeError("Missing HTTPServer section in configuration")

        if 'Logging' not in self._config:
            raise AttributeError("Missing Logging section in configuration")

        if not isinstance(self._config['Routes'], list):
            raise AttributeError("Error in Routes section in configuration")

    def _daemonize(self):
        """Daemonize the python process if we need to, otherwise set the app in
        debug mode.

        """
        # Daemonize if we need to
        if not self._options.foreground:
            utils.daemonize(pidfile=self._config.get("pidfile", None),
                            user=self._config.get("user", None),
                            group=self._config.get("group", None))
        else:
            self._config['Application']['debug'] = True

    def _fixup_configuration(self):
        """Rewrite the SSL certreqs option if it exists, do this once instead
        # of in each process like we do for imports and other things

        """
        if 'ssl_options' in self._config['HTTPServer']:
            self._fixup_ssl_config()

    def _fixup_ssl_config(self):
        """Check the config to see if SSL configuration options have been passed
        and replace none, option, and required with the correct values in
        the certreqs attribute if it is specified.

        """
        if 'cert_reqs' in self._config['HTTPServer']['ssl_options']:

            # Build a mapping dictionary
            import ssl
            reqs = {'none': ssl.CERT_NONE,
                    'optional': ssl.CERT_OPTIONAL,
                    'required': ssl.CERT_REQUIRED}

            # Get the value
            cert_reqs = \
                reqs[self._config['HTTPServer']['ssl_options']['cert_reqs']]

            # Remap the value
            self._config['HTTPServer']['ssl_options']['cert_reqs'] = cert_reqs

    def _load_configuration(self):
        """Load the configuration for the given options.

        """
        # No configuration file?
        if self._options.config is None:
            return self._load_test_config()

        # Load the configuration file
        self._config = utils.load_configuration_file(self._options.config)

        # Fixup the any of the configuration as needed
        self._fixup_configuration()

    def _load_test_config(self):
        """Load the test config from the test module returning a dictionary.

        :returns: dict

        """
        sys.stdout.write('\nConfiguration not specified, running Tinman Test '
                         'Application\n')
        from . import test
        return test.CONFIG

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

        # Parse our options and arguments
        return parser.parse_args()

    def _remove_pidfile(self):
        """Remove the PID file from the filesystem.

        """
        if 'pidfile' in self._config and \
           os.path.exists(self._config['pidfile']):
            try:
                os.unlink(self._config['pidfile'])
            except OSError as e:
                self._logger.error("Could not remove pidfile: %s", e)

    def _terminate_children(self):
        """Send term signals to all of the children and wait for them to
        shutdown.

        """
        for child in self._children:
            self._logger.debug("Sending terminate signal to %s", child.name)
            child.terminate()

        # Loop while the children are shutting down
        self._logger.debug("Waiting for children to shutdown")
        while True in [child.is_alive() for child in self._children]:
            time.sleep(0.5)

    def _tinman_process(self):
        """Create the core tinman process object, start it and return the handle

        :returns: tinman.process.TinmanProcess

        """
        tinman = process.TinmanProcess(self._config)
        tinman.start(self._config)
        return tinman

    def _wait_while_running(self):
        """Just loop and sleep while we are actively running."""
        utils.running = True
        while utils.running:
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                self._logger.info("CTRL-C pressed, shutting down.")
                break

    def run(self):
        """Run the Tinman Process"""

        # Process our command line options
        self._options, args = self._process_options()

        # Load the configuration
        self._load_configuration()

        # Check our required options
        self._check_required_configuration_parameters()

        # If we have a base path set prepend it to our Python import path
        if 'base_path' in self._config:
            sys.path.insert(0, self._config['base_path'])

        # Setup our logging
        utils.setup_logging(self._config['Logging'], self._options.foreground)

        # Setup our signal handlers
        utils.setup_signals()

        # Daemonize if we need to
        self._daemonize()

        # Create the core object
        tinman = self._tinman_process()

        # Block while running
        self._wait_while_running()

        # Tell all the children to shutdown
        self._terminate_children()

        # Remove our pidfile
        self._remove_pidfile()

        # Log that we're shutdown cleanly
        self._logger.info("tinman has shutdown")

def main():

    tinman = TinmanCLI()
    tinman.run()
