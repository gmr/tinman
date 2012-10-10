# Tinman
Tinman is a take what you need package designed to speed development of
Tornado applications.  It includes an application wrapper and a toolbox of
decorators and utilities.

## Features
- A full featured application wrapper
- Standard configuration for applications
- RequestHandler output caching
- Network address whitelisting decorator
- Method/Function debug logging decorator
- Automated connection setup for PostgreSQL, RabbitMQ and Redis
  (memcached, mongodb, mysql planned)
- Support for a External Template Loaders including Tinman's CouchDB Template Loader
- Flexible logging configuration allowing for custom formatters, filters handlers and
  setting logging levels for individual packages.

## Requirements
- clihelper
- ipaddr
- pyyaml

## Optional Dependencies
- brukva
- pika >= v0.9.5
- psycopg2 >= 2.4.2

## Unit tests
Tests are written to be run with nose and mock. They can be run with

    python setup.py nosetests

## Application Runner
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

### Configuration

#### Application Options
The following are the keys that are available to be used for your Tinman/Tornado application.

- base_path: The root of the files for the application
- cookie_secret: A salt for signing cookies when using secure cookies
- login_url: Login URL when using Tornado's @authenticated decorator
- static_path: The path to static files
- template_loader: The python module.Class to override the default template loader with
- templates_path: The path to template files
- transforms: A list of transformation objects to add to the application in module.Class format
- translations_path: The path to translation files
- ui_modules: Module for the UI modules classes (ie mysite.modules)
- xsrf_cookies: Enable xsrf_cookie mode for forms
- whitelist: List of IP addresses in CIDR notation if whitelist decorator is to be used

##### Notes
When setting the template_path or static_path values in the configuration, you
may use two variables to set the location for the values.  For example instead
of setting something like:

        Application:
            static_path: /home/foo/mywebsite

You can install your site as a non-zip safe python package and use:

        Application:
            package_name: mywebsite
            static_path: __package_path__/static
            templates_path: __package_path__/templates
            translations_path: __package_path__/translations

Or you could specify a base_path:

        Application:
            base_path: /home/foo/mywebsite
            static_path: __base_path__/static
            templates_path: __base_path__/templates
            translations_path: __base_path__/translations

If you are not going to install your app as a python package, you should set a
base_path so that tinman knows what directory to insert into the Python path to
be able to load your request handlers and such.

#### HTTP Server Options
Configure the tornado.httpserver.HTTPServer with the following options:

- no_keep_alive: Enable/Disable keep-alives
- ports: Ports to listen to, one process per port will be spawned
- ssl_options: SSL Options to pass to the HTTP Server
    - certfile: Path to the certificate file
    - keyfile: Path to the keyfile
    - cert_reqs: Certificicate required?
    - ca_certs: One of none, optional or required
- xheaders: Enable X-Header support in tornado.httpserver.HTTPServer

#### Logging Options
Logging uses the dictConfig format as specified at

  http://docs.python.org/library/logging.config.html#dictionary-schema-details

#### Route List
The route list is specified using the top-level Routes keyword. Routes consist
of a list of individual route items that may consist of mulitiple items in a route
tuple.

##### Traditional Route Tuples
The traditional route tuple, as expected by Tornado is a two or three item tuple
that includes the route to match on, the python module specified Class to use to
respond to requests on that route and an optional route settings dictionary.

###### Examples
    Routes:
      - [/, myapp.Homepage]
      - [/images, tornado.web.StaticFileHandler, {'path': '/var/www/user_images'}]

##### Complex Regex Tuples for Tinman
In order to facilitate complex regex that does not break YAML files, Tinman
supports a "re" flag in a Route tuple. If you find that your regex is breaking
your route definition, insert the string "re" before the route regex.

###### Examples
    Routes:
      -
        - re
        - /(c[a-f0-9]f[a-f0-9]{1,3}-[a-f0-9]{8}).gif
        - test.example.Pixel

#### Template Loader
The TemplateLoader configuration option is detailed the External Template Loading
section of the document.

#### Example Configuration
The following is an example tinman application configuration:

    %YAML 1.2
    ---
    user: www-data
    group: www-data
    pidfile: /var/run/tinman/tinman.pid

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
      filters:
        tinman: tinman
        pika: pika
        myapp: myapp.handlers
      formatters:
        verbose:
          format: "%(levelname) -10s %(asctime)s %(funcName) -25s: %(message)s"
        syslog:
          format: "%(levelname)s <PID %(process)d:%(processName)s> %(message)s"
      handlers:
        console:
          class: logging.StreamHandler
          formatter: verbose
          level: DEBUG
          debug_only: True
          filters:
            - myapp
            - tinman
        syslog:
          class: logging.handlers.SysLogHandler
          facility: local6
          address: /dev/log
          formatter: syslog
          level: INFO
          filters:
            - myapp
            - tinman
            - pika
        levels:
          pika: INFO

    # Automatically connect to PostgreSQL
    Postgres:
        host: localhost
        port: 5432
        dbname: postgres
        user: postgres

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
         -[/, test.example.Home]
         -
            # /c1f1-7c5d9e0f.gif
            - re
            - /(c[a-f0-9]f[a-f0-9]{1,3}-[a-f0-9]{8}).gif
            - test.example.Pixel
         -
            - .*
            - tornado.web.RedirectHandler
            - {"url": "http://www.github.com/gmr/tinman"}

## Test Application
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

## Decorators
Tinman has decorators to make web development easier.
### tinman.whitelisted
Vaidates the requesting IP address against a list of ip address blocks specified
in Application.settings

#### Example

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

### tinman.memoize
A local in-memory cache decorator. RequestHandler class method calls are cached
by name and arguments. Note that this monkey-patches the RequestHandler class
on execution and will cache the total output created including all of the
template rendering if there is anything. Local cache can be flushed with
_tinman.cache.flush()_

#### Example
    class MyClass(tornado.web.RequestHandler):

       @tinman.memoize
       def get(self, content_id):
           self.write("Hello, World")

### tinman.log_method_call
Send a logging.debug message with the class, method and arguments called.

#### Example
    class MyClass(tornado.web.RequestHandler):

        @tinman.log_method_call
        def get(self, content_id):
           self.write("Hello, World")

## Modules

### utils
A collection of helpful functions for starting, daemonizing and stopping a
Tornado application.

#### daemonize(pidfile=None, user=None, group=None)

Daemonize the application specifying the PID in the pidfile if specified,
setting the application to run as the user and group if specified.

#### setup_logging(config, debug=False)

Setup the logging module with the parameters specified in the config dictionary.
If debug is specified as True, output will be to stdout using the Tornado
colored output if available and all other logging methods such as file or syslog
will be disabled.

##### config dictionary format

    directory:   Optional log file output directory
    filename:    Optional filename, not needed for syslog
    format:      Logging output format
    level:       One of debug, error, warning, info
    handler:     Optional handler
    syslog:      If handler == syslog, parameters for syslog
        address:   Syslog address
        facility:  Syslog facility

#### shutdown()

Will call the stop() method of all child objects added to the
tinman.utils.children list. This is useful for multi-processing apps to
make sure that all children shutdown when a signal is called on the parent

#### setup_signals()

Registers the shutdown function on SIGTERM and registers a rehash handler
on SIGHUP. To specify the rehash handler, assign a callback to
tinman.utils.rehash_handler.


### Redis Handler

The redis handler adds built-in support for Redis using the tornado-redis library.

#### Example Configuration Snippet

    Application:
      redis:
        host: localhost
        port: 6379
        db: 0

#### Example Code Example

    import datetime
    from tinman.handlers import redis
    from tornado import web

    class DefaultHandler(redis.RedisRequestHandler):

        @web.asynchronous
        def get(self, *args, **kwargs):
            self._redis_set('last_request', datetime.datetime.now().isoformat())
            self.set_status(204)
            self.finish()


### CouchDB Loader

Tinman includes tinman.loader.CouchDBLoader to enable the storage of templates
in CouchDB to provide a common stemplate storage mechanism across multiple
servers.

Templates stored in CouchDB are stored with the full path as the document key
and the template value is stored in the document using the key "template"

When storing templates in CouchDB it is important that the forward-slash (/) is
replaced with a colon (:) as the key value in CouchDB, or it will not find the
stored file.

For example a template with a filesystem path of /foo/bar/template.html would
be stored with a key of foo:bar:template.html in CouchDB but still referenced
as /foo/bar/template.html everywhere else.

#### Example templates document from CouchDB

    {
       "_id": "base.html",
       "_rev": "1-18d104181a15f617a929c221d01423da",
       "template": "<html>\n  <head>\n    <title>{% block \"title\" %}Title{% end %}</title>\n  </head>\n  <body>\n    <h1>Hello, World!</h1>\n  </body>\n</html>"
    },
    {
       "_id": "pages:home.html",
       "_rev": "2-c3c06f5a6d6a7b8149e0a700c67aeb41",
       "template": "{%  extends \"base.html\" %} \n{% block title %}Homepage{% end %}"
    }
