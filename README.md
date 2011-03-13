Tinman
======
A collection of useful decorators and modules for Tornado.

Requirements
------------
- ipaddr
- pyyaml

Decorators
----------

- tinman.whitelisted: Vaidates the requesting IP address against a list of ip
  address blocks specified in Application.settings

  Example:

        # Define the whitelist as part of your application settings
        settings['whitelist'] = ['10.0.0.0/8',
                                 '192.168.1.0/24',
                                 '1.2.3.4/32']

        application = Application(routes, **settings)

        # Specify the decorator in each method of your RequestHandler class
        # where you'd like to enforce the whitelist
        class MyClass(tornado.web.RequestHandler):

          @tinman.whitelisted
          def get(self):
              self.write("IP was whitelisted")

- tinman.memoize: A local in-memory cache decorator. RequestHandler class
  method calls are cached by name and arguments. Note that this monkey-patches
  the RequestHandler class on execution and will cache the total output created
  including all of the template rendering if there is anything. Local cache
  can be flushed with "tinman.cache.flush()"

  Example:

        class MyClass(tornado.web.RequestHandler):

           @tinman.memoize
           def get(self, content_id):
               self.write("Hello, World")

 - tinman.log_method_call: Send a logging.debug message with the class, method
   and arguments called.

   Example:

        class MyClass(tornado.web.RequestHandler):

            @tinman.log_method_call
            def get(self, content_id):
               self.write("Hello, World")


Modules
-------

- utils: A collection of helpful functions for starting, daemonizing and
  stopping a Tornado application.

  Methods:

  - daemonize(pidfile=None, user=None, group=None)

    Daemonize the application specifying the PID in the pidfile if specified,
    setting the application to run as the user and group if specified.

  - setup_logging(config, debug=False)

    Setup the logging module with the parameters specified in the config
    dictionary. If debug is specified as True, output will be to stdout
    using the Tornado colored output if available and all other logging methods
    such as file or syslog will be disabled.

    config dictionary format:

    * directory:   Optional log file output directory
    * filename:    Optional filename, not needed for syslog
    * format:      Format for non-debug mode
    * level:       One of debug, error, warning, info
    * handler:     Optional handler
    * syslog:      If handler == syslog, parameters for syslog
      * address:   Syslog address
      * facility:  Syslog facility

  - shutdown()

    Will call the stop() method of all child objects added to the
    tinman.utils.children list. This is useful for multi-processing apps to
    make sure that all children shutdown when a signal is called on the parent

  - def setup_signals()

    Registers the shutdown function on SIGTERM and registers a rehash handler
    on SIGHUP. To specify the rehash handler, assign a callback to
    tinman.utils.rehash_handler.

