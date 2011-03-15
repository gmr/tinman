#!/usr/bin/env
__author__ = 'Gavin M. Roy'
__email__ = 'gmr@myyearbook.com'
__since__ = '03/14/2011'
__version__ = "2.0"

# Tinman direct imports for shorter access
from cache import memoize
from whitelist import whitelisted
from utils import log_method_call

# Import utils for main use
import utils

# Base imports for running the tinman app runner
from logging import debug, error, info
from multiprocessing import Process
from optparse import OptionParser
from os import unlink
from os.path import exists
from signal import signal, SIGTERM
from sys import stderr, exit
from time import sleep
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import Application

# Handle for our process wide ioloop global
ioloop = None


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
    application = Application(routes, **settings)

    # Start the HTTP Server
    info("Starting Tornado HTTPServer on port %i" % port)
    http_server = HTTPServer(application)
    http_server.listen(port)

    # Get a handle to the instance of IOLoop
    ioloop = IOLoop.instance()

    # Start the IOLoop
    ioloop.start()


def main(*args):

    # Setup optparse
    usage = "usage: %prog -c <configfile> [options]"
    version_string = "%%prog %s" % __version__
    description = "tinman is a Tornado application runner"

    # Create our parser and setup our command line options
    parser = OptionParser(usage=usage,
                          version=version_string,
                          description=description)

    parser.add_option("-c", "--config",
                      action="store", dest="config",
                      help="Specify the configuration file for use")

    parser.add_option("-f", "--foreground",
                      action="store_true", dest="foreground", default=False,
                      help="Run interactively in console")

    # Parse our options and arguments
    options, args = parser.parse_args()

    # No configuration file?
    if options.config is None:
        stderr.write('\nERROR: Missing configuration file\n\n')
        parser.print_help()
        exit(1)

    # Load in the YAML config file
    config = utils.load_configuration_file(options.config)

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
            except OSError as err:
                error("Could not remove pidfile: %s", err)

    # Log that we're shutdown cleanly
    info("tinman has shutdown")


if __name__ == "__main__":
    main()
