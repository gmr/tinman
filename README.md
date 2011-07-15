Tinman
======
Tinman is a take what you need package designed to speed development of
Tornado applications.  It includes an application wrapper and a toolbox of
decorators and utilities.

Features
--------
- RequestHandler output caching
- Network address whitelisting decorator
- Method/Function debug logging decorator
- A full featured application wrapper
- Automated connection setup for RabbitMQ and Redis
  (memcached, mongodb, mysql, postgresql planned)

Requirements
------------
- ipaddr
- pyyaml

Optional Dependencies
---------------------
- pika >= v0.9.5

Application Runner
------------------
The tinman application runner works off a YAML configuration file format and
provides a convenient interface for running tornado applications interactively
or as a daemon.

    Command Line Syntax:

        Usage: tinman -c <configfile> [options]

        Tornado application wrapper

        Options:
          --version             show program's version number and exit
          -h, --help            show this help message and exit
          -c CONFIG, --config=CONFIG
                                Specify the configuration file for use
          -f, --foreground      Run interactively in console

    Configuration File Syntax:

        %YAML 1.2
        ---
        Application:
            base_path: /home/foo/mywebsite
            debug: True
            xsrf_cookies: False
            # Any other vaidate Tornado application setting item

        HTTPServer:
            no_keep_alive: False
            ports: [8000,8001]
            xheaders: True

        Logging:
            #filename: log.txt
            format: "%(module)-10s# %(lineno)-5d %(levelname) -10s %(asctime)s  %(message)s"
            # Valid values: debug, info, warning, error, critical
            level: debug
            handler: syslog
            syslog:
                address: /dev/log
                facility: LOG_LOCAL6

        # Automatically connect to RabbitMQ
        RabbitMQ:
            host: localhost
            port: 5672
            username: guest
            password: guest
            virtual_host: /

        # Automatically connect to Redis
        Redis:
            host: localhost
            port: 6379
            db: 0

        Routes:
             -
                - /
                - test.example.Home
             -
                # /c1f1-7c5d9e0f.gif
                - re
                - /(c[a-f0-9]f[a-f0-9]{1,3}-[a-f0-9]{8}).gif
                - test.example.Pixel
             -
                - .*
                - tornado.web.RedirectHandler
                - {"url": "http://www.github.com/gmr/tinman"}

Test Application
----------------
The tinman application runner has a built in test application. To see if the
module is setup correctly simply run:

    tinman -f

In your console you should see output similar to:

    Configuration not specified, running Tinman Test Application
    utils       # 247   INFO      2011-06-11 23:25:26,164  Log level set to 10
    cli         # 145   INFO      2011-06-11 23:25:26,164  Starting Tinman v0.2.1 process for port 8000
    cli         # 154   DEBUG     2011-06-11 23:25:26,169  All children spawned
    application # 106   DEBUG     2011-06-11 23:25:26,170  Initializing route: / with tinman.test.DefaultHandler
    application # 36    INFO      2011-06-11 23:25:26,171  Appending handler: ('/', <class 'tinman.test.DefaultHandler'>)
    cli         # 171   INFO      2011-06-11 23:25:26,174  Starting Tornado v1.2.1 HTTPServer on port 8000
    web         # 1235  INFO      2011-06-11 23:25:32,782  200 GET / (127.0.0.1) 1.24ms

You should now be able to access a test webpage on port 8000. CTRL-C will exit.

Configuration Notes
-------------------
When setting the template_path or static_path values in the configuration, you
may use two variables to set the location for the values.  For example instead
of setting something like:

        Application:
            static_path: /home/foo/mywebsite

You can install your site as a non-zip safe python package and use:

        Application:
            package_name: mywebsite
            static_path: __package_path__/static
            template_path: __package_path__/templates

Or you could specify a base_path:

        Application:
            base_path: /home/foo/mywebsite
            static_path: __base_path__/static
            template_path: __template_path__/templates

If you are not going to install your app as a python package, you should set a
base_path so that tinman knows what directory to insert into the Python path to
be able to load your request handlers and such.

Decorators
----------
__tinman.whitelisted__

Vaidates the requesting IP address against a list of ip address blocks specified
in Application.settings

_Example_

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

In addition you may add the whitelist right into the configuration file:

    Application:
        whitelist:
          - 10.0.0.0/8
          - 192.168.1.0/24
          - 1.2.3.4/32

__tinman.memoize__

A local in-memory cache decorator. RequestHandler class method calls are cached
by name and arguments. Note that this monkey-patches the RequestHandler class
on execution and will cache the total output created including all of the
template rendering if there is anything. Local cache can be flushed with
_tinman.cache.flush()_

 _Example_

    class MyClass(tornado.web.RequestHandler):

       @tinman.memoize
       def get(self, content_id):
           self.write("Hello, World")

__tinman.log_method_call__

Send a logging.debug message with the class, method and arguments called.

_Example_

    class MyClass(tornado.web.RequestHandler):

        @tinman.log_method_call
        def get(self, content_id):
           self.write("Hello, World")


Modules
-------
__utils__

A collection of helpful functions for starting, daemonizing and stopping a
Tornado application.

**daemonize(pidfile=None, user=None, group=None)**

Daemonize the application specifying the PID in the pidfile if specified,
setting the application to run as the user and group if specified.

**setup_logging(config, debug=False)**

Setup the logging module with the parameters specified in the config dictionary.
If debug is specified as True, output will be to stdout using the Tornado
colored output if available and all other logging methods such as file or syslog
will be disabled.

_config dictionary format_

    directory:   Optional log file output directory
    filename:    Optional filename, not needed for syslog
    format:      Format for non-debug mode
    level:       One of debug, error, warning, info
    handler:     Optional handler
    syslog:      If handler == syslog, parameters for syslog
        address:   Syslog address
        facility:  Syslog facility

**shutdown()**

Will call the stop() method of all child objects added to the
tinman.utils.children list. This is useful for multi-processing apps to
make sure that all children shutdown when a signal is called on the parent

**setup_signals()**

Registers the shutdown function on SIGTERM and registers a rehash handler
on SIGHUP. To specify the rehash handler, assign a callback to
tinman.utils.rehash_handler.

Auto-Setup of Services
----------------------
In order to facilitate a quick development process, the tinman application now
has the concept of auto-setup and connect services. Initially, RabbitMQ is the
only connectivity that is supported (via the Pika library). It is intended to
add support for all major service types that have asynchronous support for the
Tornado IO loop.

__RabbitMQ__

To setup an automatic connection to RabbitMQ simply include a RabbitMQ section
in your configuration file:

    RabbitMQ:
        host: localhost
        port: 5672
        username: guest
        password: guest
        virtual_host: /

When the application is constructed, it will connect to RabbitMQ and assign
the connection and channel to a standard object called tinman which is an
attribute of the application.

We construct a copy of a tinman specific object using the tinman.clients.rabbitmq.RabbitMQ
class. Currently this is only setup to publish messages, though it is the intent
to add the ability to consume messages asychronously as well. This object is
accessed from a request handler as: self.application.tinman.rabbitmq

For publishing messages, only one command is required: RabbitMQ.publish_message

If you pass in a dictionary or list, the message will be auto-JSON encoded
and the mimetype will be set as application/json.

_Parameters_

 - exchange: RabbitMQ exchange to publish to
 - routing_key: RabbitMQ routing key to use in publishing message
 - message: The message itself to send
 - mimetype: The mimetype of the message (default: text/plain)
 - mandatory: AMQP Basic.Publish mandatory field
 - immediate: AMQP Basic.Publish immediate field

_Returns_

    None

_Example_

    self.application.tinman.rabbitmq.publish_message(self._exchange,
                                                     routing_key,
                                                     event)

__Redis__

To setup an automatic connection to Redis siply include a Redis section in your
configuration file:

    Redis:
        host: localhost
        port: 6379
        db: 0
        password: foo

When the application is constructed, it will connect to Redis and assign
the connection and channel to a standard object called tinman which is an
attribute of the application.

We construct a copy of a tinman specific object using the tinman.clients.redis.Redis
class. This object is accessed from a request handler as self.application.tinman.redis

This class requires the asynchronous brukva client from https://github.com/evilkost/brukva

_Example_

    from tornado import web

    class RedisTest(web.RequestHandler):

        def initialize(self):
            # Set a more handy redis handle
            self.redis = self.application.tinman.redis.client

        @web.asynchronous
        def get(self, key):

            # Make an asynchronous redis request
            self.redis.get(key, self.on_redis_response)

        def on_redis_response(self, response):
            """Since we're fully async here, when redis comes back with our response
            we'll process it in this function.

            """
            # If we could not find the response code
            if not response:
                self.send_error(404)

            # Write the redis value out as a key/value pair in JSON
            self.write({key: response})

            # Done
            self.finish()
