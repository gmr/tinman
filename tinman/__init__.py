#!/usr/bin/env
__author__ = 'Gavin M. Roy'
__email__ = 'gmr@myyearbook.com'
__since__ = '03/14/2011'
__version__ = "2.0"

# Tinman direct imports for shorter access
from cache import memoize
from whitelist import whitelisted
from utils import log_method_call
from utils import import_namespaced_class

# Import utils for main use
import utils

# Base imports for running the tinman app runner
from logging import debug, error, info
from multiprocessing import Process
from optparse import OptionParser
from os import unlink
from os.path import exists, dirname, realpath
from signal import signal, SIGTERM
from sys import stderr, exit
from time import sleep
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import Application

# Handle for our process wide ioloop global
ioloop = None


class TinmanApplication(Application):

    def __init__(self, routes=None, **settings):

        # If we have routes, import the classes and set everything up real nice
        if routes:

            # Validate it's a list
            if not isinstance(routes, list):
                raise ValueError("Routes should be a list of tuples")

            handlers = []
            for parts in routes:

                # Return the reference to the python class at the end of the
                # namespace. eg foo.Baz, foo.bar.Baz
                try:
                    parts[1] = import_namespaced_class(parts[1])
                except ImportError as err:
                    error("Skipping %s due to import error: %s",
                          parts[1], err)
                    continue

                # Append our handle stack
                info('Appending handler: %r', parts)
                handlers.append(tuple(parts))

            # Set the app version from the version setting in this file
            if 'version' not in settings:
                settings['version'] = __version__

            # Set the base path for use inside the app since all code locations
            # are not relative
            if 'base_path' not in settings:
                settings['base_path'] = dirname(realpath(__file__))

            # If we have a static_path
            if 'static_path' in settings:
                # Replace __base_path__ with the path this is running from
                settings['static_path'] =\
                    settings['static_path'].replace('__base_path__',
                                                    settings['base_path'])

        # If we specified the UI modules module we need to import it
        if 'ui_modiles' in settings:
            try:
                # Assign the modules to the import
                settings['ui_modules'] = \
                    import_namespaced_class(settings['ui_modules'])
            except ImportError as err:
                error("Error importing UI Modules %s: %s",
                      settings['ui_modules'], err)

        # Create our Application for this process
        Application.__init__(self, handlers, **settings)


def _shutdown_signal_handler(signum, frame):
    """
    Called on SIGTERM to shutdown the sub-process
    """
    if ioloop:
        ioloop.stop()


def start(routes, settings, http_config, port):
    global ioloop

    # Setup a signal handler to cleanly shutdown this process
    signal(SIGTERM, _shutdown_signal_handler)

    # Start our application
    application = TinmanApplication(routes, **settings)

    # Start the HTTP Server
    info("Starting Tornado HTTPServer on port %i" % port)
    http_server = HTTPServer(application)
    http_server.listen(port)

    # Get a handle to the instance of IOLoop
    ioloop = IOLoop.instance()

    # Start the IOLoop
    try:
        ioloop.start()
    except KeyboardInterrupt:
        debug("Keyboard Interrupt received, shutting down child Process")


def main(*args):

    # Setup optparse
    usage = "usage: %prog -c <configfile> [options]"
    version_string = "%%prog %s" % __version__
    description = "Tornado application runner"

    # Create our parser and setup our command line options
    parser = OptionParser(usage=usage,
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
    options, args = parser.parse_args()

    # No configuration file?
    if options.config is None:
        stderr.write('\nERROR: Missing configuration file\n\n')
        parser.print_help()
        exit(1)

    # Load in the YAML config file
    config = utils.load_configuration_file(options.config)

    # Required

    if 'Application' not in config:
        raise AttributeError("Missing Application section in configuration")

    if 'HTTPServer' not in config:
        raise AttributeError("Missing HTTPServer section in configuration")

    if 'Logging' not in config:
        raise AttributeError("Missing Logging section in configuration")

    if not options.route_decorator and 'Routes' not in config:
        raise AttributeError("Missing Routes section in configuration")

    if not options.route_decorator and \
       not isinstance(config['Routes'], 'list'):
        raise AttributeError("Error in Routes section in configuration")

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

    # Loop through and kick off our processes
    children = []
    for port in config['HTTPServer']['ports']:
        debug("Starting process for port %i" % port)
        # Kick off the child process
        child = Process(target=start,
                        name="tinman-%i" % port,
                        args=(config['Routes'],
                              config['Application'],
                              config['HTTPServer'],
                              port))
        children.append(child)
        child.start()
    debug("All children spawned")

    # Have a main event loop for dealing with stats
    utils.running = True
    while utils.running:
        try:
            sleep(1)
        except KeyboardInterrupt:
            info("CTRL-C pressed, shutting down.")
            break

    # Tell all the children to shutdown
    for child in children:
        debug("Sending terminate signal to %s", child.name)
        child.terminate()

    # Loop while the children are shutting down
    debug("Waiting for children to shutdown")
    while True in [child.is_alive() for child in children]:
        sleep(0.5)

    # Remove our pidfile
    if 'pidfile' in config:
        if exists(config['pidfile']):
            try:
                unlink(config['pidfile'])
            except OSError as e:
                error("Could not remove pidfile: %s", e)

    # Log that we're shutdown cleanly
    info("tinman has shutdown")


if __name__ == "__main__":
    main()
