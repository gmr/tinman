#!/usr/bin/env python
"""
Generic Tornado Application Controller

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
__version__ = 0.1

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

import project.apps
import project.handler
import project.modules

# List to hold the child processes
children = []

class Application(tornado.web.Application):
 
    def __init__(self, config):
        
        # Our main handler list
        handlers = [
            (r"/", project.apps.Home),
            (r".*", project.handler.ErrorHandler ) # Should always be last
        ]
        
        # Site settings
        settings = dict(
            debug                      = config['debug'],
            cookie_secret              = config['cookie_secret'],
            static_path                = config['static_path'],
            ui_modules                 = project.modules,
            version                    = __version__,
            xsrf_cookies               = config['xsrf_cookies']
        )
        
        tornado.web.Application.__init__(self, handlers, **settings)


def runapp(config, port):

    try:
        http_server = tornado.httpserver.HTTPServer(Application(config), no_keep_alive = config['no_keep_alive'])
        http_server.listen(port)
        tornado.ioloop.IOLoop.instance().start()

    except KeyboardInterrupt:
        shutdown()
        
    except Exception as out:
        logging.error(out)
        shutdown()
        
def shutdown():

    logging.debug('Shutting down')
    for child in children:
        try:
            if child.is_alive():
                logging.debug("terminating child: %s" % child.name)
                child.terminate()
        except AssertionError:
            logging.error('Dead child encountered')

    logging.debug('All children have shutdown, now terminating controlling application')
    sys.exit(0)


def signal_handler(sig, frame): 
    
    # We can shutdown from sigterm or keyboard interrupt so use a generic function
    shutdown()


if __name__ == "__main__":

    usage = "usage: %prog -c <configfile> [options]"
    version_string = "%%prog %s" % __version__
    description = "Project Name"
    
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
        print "Please provide a configuration file"
        print usage
        sys.exit(1)

    # try to load the config file. 
    try:
        stream = file(options.config, 'r')
        config = yaml.load(stream)
        stream.close()
    except IOError:
        sys.stderr.write('Invalid or missing configuration file \"%s\"' % options.config)
        sys.exit(1)

    # Set logging levels dictionary
    logging_levels = { 
                        'debug':    logging.DEBUG,
                        'info':     logging.INFO,
                        'warning':  logging.WARNING,
                        'error':    logging.ERROR,
                        'critical': logging.CRITICAL
                     }
    
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
    if config['Logging'].has_key('handler'):
        
        # If we want to syslog
        if config['Logging']['handler'] == 'syslog':
 
            from logging.handlers import SysLogHandler
 
            # Create the syslog handler            
            logging_handler = SysLogHandler( address=config['Logging']['syslog']['address'], facility = SysLogHandler.LOG_LOCAL6 )
            
            # Add the handler
            logger = logging.getLogger()
            logger.addHandler(logging_handler)

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
                print 'project.py daemon has started - PID # %d.' % pid
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

    # Load the locales
    logging.debug('Loading translations')
    tornado.locale.load_translations(
        os.path.join(os.path.dirname(__file__), "translations"))

    # Handle signals
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler) 

    # Tell multiprocessing we want to use logging
    multiprocessing.get_logger()

    # Kick off our application servers
    for port in config['ports']:
        logging.debug('Spawning application on port %i' % port)
        proc = multiprocessing.Process(target=runapp, args=(config, port))
        proc.start()
        children.append(proc)       