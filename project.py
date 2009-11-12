#!/usr/bin/env python
"""
Generic Tornado Application Controller

(c) 2009 Gavin M. Roy All Rights Reserved
"""

__author__  = "Gavin M. Roy"
__date__    = 2009-11-12
__version__ = 0.1

import optparse
import os
import sys
import tornado.httpserver
import tornado.ioloop
import tornado.locale
import tornado.web

import project.apps
import project.modules

class Application(tornado.web.Application):
 
    def __init__(self):
        
        # Our main handler list
        handlers = [
            (r"/", project.apps.Home),
        ]
        
        # Site settings
        settings = dict(
            debug                      = True,
            cookie_secret              = "some_value_here",
            static_path                = "~/Source/tornado-project-stub/static",
            ui_modules                 = project.modules,
            xsrf_cookies               = True
        )
        
        tornado.web.Application.__init__(self, handlers, **settings)

if __name__ == "__main__":

    usage = "usage: %prog [options]"
    version_string = "%%prog %s" % __version__
    description = "Project Name"
    
    # Create our parser and setup our command line options
    parser = optparse.OptionParser(usage=usage,
                         version=version_string,
                         description=description)
 
    parser.add_option("-c", "--console",
                        action="store_true", dest="console", default=False,
                        help="Run interactively in console for debugging purposes")                                                                                                                                 
 
    # Parse our options and arguments                                                                        
    options, args = parser.parse_args()
    
    # Fork our process to detach if not told to stay in foreground
    if not options.console:
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
        os.chdir('~/Source/tornado-project-stub/') 
        os.setsid()
        os.umask(0) 
 
        # Close stdin            
        sys.stdin.close()
        
        # Redirect stdout, stderr
        sys.stdout = open('/dev/null', 'a')
        sys.stderr = open('/dev/null', 'a')

    # Load the locales
    tornado.locale.load_translations(
        os.path.join(os.path.dirname(__file__), "translations"))
    
    # Kick of the HTTP Server and Application                        
    http_server = tornado.httpserver.HTTPServer(Application(), no_keep_alive = False)
    http_server.listen(8080)
    tornado.ioloop.IOLoop.instance().start()