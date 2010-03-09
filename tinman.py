#!/usr/bin/env python
"""
Tinman Controller

Copyright (c) 2009, Gavin M. Roy
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
Neither the name of the Insider Guides, Inc. nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

__author__  = "Gavin M. Roy"
__email__   = "gavinmroy@gmail.com"
__date__    = "2009-11-10"
__appname__ = 'tinman'
__version__ = '0.3'

import logging
import multiprocessing
import optparse
import os
import signal
import sys
import tornado.httpserver
import tornado.ioloop
import tornado.locale
import tornado.web
import yaml

# List to hold the child processes
children = []

class Application(tornado.web.Application):

    def __init__(self, config):

        # Our main handler list
        handlers = []
        for handler in config['RequestHandlers']:

            # Split up our string containing the import and class
            p = handler[1].split('.')

            # Handler must be in the format: foo.bar.baz where
            # foo is the import dir, bar is the file and baz is the class
            if len(p) != 3:
                logging.error('Import module name error')

            # Build the import string
            s = '.'.join(p[0:-1])
            # Import the module, getting the file from the __dict__
            logging.debug('Importing: %s.%s' % (s, p[-1]))
            m = __import__(s, fromlist=['.'.join(p[1:-1])])

            # Get the handle to the class
            h = getattr(m,p[-1])

            # Append our handle stack
            logging.debug('Appending handler for "%s": %s.%s' % (handler[0], s, p[-1]))
            handlers.append((handler[0], h))

        # Get the dictionary from our YAML file
        settings = config['Application']

        # Set the app version from the version setting in this file
        settings['version'] = __version__

        # Set the base path for use inside the app since all code locations are not relative
        settings['base_path'] = os.path.dirname(os.path.realpath(__file__))

        # If we have a static_path
        if settings.has_key('static_path'):
            # Replace __base_path__ with the path this is running from
            settings['static_path'] = settings['static_path'].replace('__base_path__',
                                                                      settings['base_path'])

        # If we specified the UI modules, we need to import it not pass a string
        if settings.has_key('ui_modules'):

            # Split up our string containing the import and class
            p = settings['ui_modules'].split('.')

            # Module must be in the format: foo.bar
            # foo is the import dir, bar is the file containing module classes
            if len(p) != 2:
                logging.error('Import module name error')

            # Import the module, getting the file from the __dict__
            m = __import__(settings['ui_modules'], fromlist=[p[1]])

            # Assign the modules to the import
            settings['ui_modules'] = m

        # Create our Application for this process
        tornado.web.Application.__init__(self, handlers, **settings)


def runapp(config, port):

    try:
        http_server = tornado.httpserver.HTTPServer(Application(config),
                                                    no_keep_alive=config['HTTPServer']['no_keep_alive'],
                                                    xheaders=config['HTTPServer']['xheaders'])
        http_server.listen(port)
        tornado.ioloop.IOLoop.instance().start()

    except KeyboardInterrupt:
        shutdown()

    except Exception as out:
        logging.error(out)
        shutdown()

def shutdown():

    logging.debug('%s: shutting down' % __appname__)
    for child in children:
        try:
            if child.is_alive():
                logging.debug("%s: Terminating child: %s" % (__appname__, child.name))
                child.terminate()
        except AssertionError:
            logging.error('%s: Dead child encountered' % __appname__)

    logging.debug('%s: shutdown complete' % __appname__)
    sys.exit(0)


def signal_handler(sig, frame):

    # We can shutdown from sigterm or keyboard interrupt so use a generic function
    shutdown()


if __name__ == "__main__":

    usage = "usage: %prog -c <configfile> [options]"
    version_string = "%%prog %s" % __version__
    description = "Tinman is a meta-framework on top of Tornado"

    # Create our parser and setup our command line options
    parser = optparse.OptionParser(usage=usage,
                         version=version_string,
                         description=description)

    parser.add_option("-c", "--config",
                        action="store", dest="config",
                        help="Specify the configuration file for use")

    parser.add_option("-f", "--foreground",
                        action="store_true", dest="foreground", default=False,
                        help="Run interactively in console for debugging purposes")

    # Parse our options and arguments
    options, args = parser.parse_args()

    if options.config is None:
        sys.stderr.write('Missing configuration file\n')
        print usage
        sys.exit(1)

    # try to load the config file.
    try:
        stream = file(options.config, 'r')
        config = yaml.load(stream)
        stream.close()
    except IOError, err:
        sys.stderr.write('Configuration file not found "%s"\n' % options.config)
        sys.exit(1)
    except yaml.scanner.ScannerError, err:
        sys.stderr.write('Invalid configuration file "%s":\n%s\n' % (options.config, err))
        sys.exit(1)

    # Set logging levels dictionary
    logging_levels = { 'debug':    logging.DEBUG,
                       'info':     logging.INFO,
                       'warning':  logging.WARNING,
                       'error':    logging.ERROR,
                       'critical': logging.CRITICAL }

    # Get the logging value from the dictionary
    logging_level = config['Logging']['level']
    config['Logging']['level'] = logging_levels.get( config['Logging']['level'],
                                                     logging.NOTSET )

    # If the user says verbose overwrite the settings.
    if options.foreground:

        # Set the debugging level to verbose
        config['Logging']['level'] = logging.DEBUG

        # If we have specified a file, remove it so logging info goes to stdout
        if config['Logging'].has_key('filename'):
            del config['Logging']['filename']

    else:
        # Build a specific path to our log file
        if config['Logging'].has_key('filename'):
            config['Logging']['filename'] = os.path.join( os.path.dirname(__file__),
                                                          config['Logging']['directory'],
                                                          config['Logging']['filename'] )

    # Pass in our logging config
    logging.basicConfig(**config['Logging'])
    logging.info('Log level set to %s' % logging_level)

    # If we have supported handler
    if config['Logging'].has_key('handler') and not options.foreground:

        # If we want to syslog
        if config['Logging']['handler'] == 'syslog':

            facility = config['Logging']['syslog']['facility']
            import logging.handlers as handlers

            # If we didn't type in the facility name
            if handlers.SysLogHandler.facility_names.has_key(facility):

                # Create the syslog handler
                syslog = handlers.SysLogHandler(address=config['Logging']['syslog']['address'],
                                                facility = handlers.SysLogHandler.facility_names[facility])

                # Get the default logger
                default_logger = logging.getLogger('')

                # Add the handler
                default_logger.addHandler(syslog)

                # Remove the default stream handler
                for handler in default_logger.handlers:
                    if isinstance(handler, logging.StreamHandler):
                        default_logger.removeHandler(handler)

            else:
                logging.error('%s: Invalid SysLog facility name specified, syslog logging aborted' % __appname__)

    # Fork our process to detach if not told to stay in foreground
    if not options.foreground:
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError, e:
            sys.stderr.write("Could not fork: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        # Second fork to put into daemon mode
        try:
            pid = os.fork()
            if pid > 0:
                # exit from second parent, print eventual PID before
                print '%s: daemon has started - PID # %d.' % ( __appname__, pid )

                # Write a pidfile out
                filename = os.path.join(os.path.dirname(__file__), "pids/%s.pid" % __appname__)
                with open(filename, 'w') as pid_file:
                    pid_file.write('%i\n' % pid)
                    pid_file.close()

                # Exit the parent project
                sys.exit(0)
        except OSError, e:
            sys.stderr.write("Could not fork: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        # Detach from parent environment
        os.chdir(os.path.dirname(__file__))
        os.setsid()
        os.umask(0)

        # Close stdin
        sys.stdin.close()

        # Redirect stdout, stderr
        sys.stdout = open('/dev/null', 'a')
        sys.stderr = open('/dev/null', 'a')
    else:
        logging.info('%s: has started in interactive mode' % __appname__)

    # Load the locales
    logging.info('%s: Loading translations' % __appname__)
    try:
        tornado.locale.load_translations(os.path.join(os.path.dirname(__file__),
                                         "translations"))
    except OSError:
        logging.info('%s: No translations found' % __appname__)

    # Handle signals
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Kick off our application servers
    for port in config['HTTPServer']['ports']:
        logging.info('%s: spawning on port %i' % (__appname__, port))
        proc = multiprocessing.Process(target=runapp, args=(config, port))
        proc.start()
        children.append(proc)
