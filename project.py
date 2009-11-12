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
__date__    = 2009-11-10
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