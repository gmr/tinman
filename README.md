# Tinman
Tinman adds a little more stack to Tornado. It is designed to speed development
of Tornado applications. It includes an application wrapper and a toolbox of
decorators and utilities.

## 0.9+ Version Warning
The configuration file syntax has changed and the structure of the package has
changed. Please test your applications if you are upgrading from 0.4 or
previous.

## Features
- A full featured application wrapper
- Standard configuration for applications
- Built-in configurable session management
- A command-line tool, tinman-init that will create a skeleton app structure
  with the initial package and setup.py file.
- RequestHandler output caching
- Network address whitelisting decorator
- Method/Function debug logging decorator
- Handlers with automated connection setup for PostgreSQL, RabbitMQ and Redis
- Support for a External Template Loaders including Tinman's CouchDB Template Loader
- Flexible logging configuration allowing for custom formatters, filters handlers and
  setting logging levels for individual packages.
- Built in support for NewRelic's Python agent library

## Installation
Install via pip or easy_install:

    pip install tinman

## Module Descriptions

- tinman
  - application: Application extends tornado.web.Application, handling the auto-loading of configuration for routes, logging, translations, etc.
  - controller: Core tinman application controller.
  - decorators: Authentication, memoization and whitelisting decorators.
  - exceptions: Tinman specific exceptions
  - handlers: Request handlers which may be used as the base handler or mix-ins.
    - rabbitmq: A request handler that implements a pika connection for publishing, consuming or other interaction with RabbitMQ.
    - redis: A request handler that uses tornado-redis for use with redis.
    - session: A request handler with built-in session management.
  - loaders: A library of custom template loaders, currently only CouchDB is supported.
  - process: Invoked by the controller, each Tinman process is tied to a specific HTTP server port.
  - session: Session adapters and serialization mixins
  - utilities: Command line utilities

## Requirements
- clihelper
- ipaddr
- python_daemon
- pyyaml

## Optional Dependencies
- Heapy: guppy,
- LDAP: python-ldap,
- MsgPack Sessions: msgpack,
- NewRelic: newrelic>=1.12.0',
- PostgreSQL: psycopg2,
- RabbitMQ: pika>=0.9.9,
- Redis: tornado-redis,
- Redis Sessions: redis

### Installing optional Dependencies
Use pip to install dependencies:

    pip install 'tinman[Dependency Name]'

For example:

    pip install 'tinman[RabbitMQ]'

## Application Runner
The tinman application runner works off a YAML configuration file format and
provides a convenient interface for running tornado applications interactively
or as a daemon.

Command Line Syntax:

    Usage: usage: tinman -c <configfile> [options]

    Tinman adds a little more stack to Tornado

    Options:
      -h, --help            show this help message and exit
      -c CONFIGURATION, --config=CONFIGURATION
                            Path to the configuration file
      -f, --foreground      Run interactively in console
      -n NEWRELIC, --newrelic=NEWRELIC
                            Path to newrelic.ini to enable NewRelic
                            instrumentation
      -p PATH, --path=PATH  Path to prepend to the Python system path

### Example Handlers

#### Session
Sessions will automatically load on prepare and save on finish. If you extend
the SessionHandler and need to use prepare or finish, make sure to call
super(YourClass, self).prepare() and super(YourClass, self).on_finish() in
your extended methods. By using the session mixins you can change the default
session behavior to use different types of storage backends and serializers.

    from tinman.handlers import session
    from tornado import web

    class Handler(session.SessionHandler):

      @web.asynchronous
      def get(self, *args, **kwargs):

          # Set a session attribute
          self._session.username = 'foo'
          self._session.your_variable = 'bar'

          self.write({'session_id': self._session.id,
                      'your_variable': self._session.your_variable})
          self.finish()

      def prepare(self):
          super(Handler, self).on_finished()
          # Do other stuff here

      def prepare(self):
          super(Handler, self).prepare()
          # Do other stuff here

#### Heapy
The Heapy handler uses the guppy library to inspect the memory stack of your
running Tinman application, providing a JSON document back with the results.
It is *very* slow and blocking and can take many *MINUTES* to complete so it
should be used very sparingly and if used on a production application, with
the whitelist decorator.

To use the Heapy handler, just add the route to your configuration:

      - [/heapy, tinman.handlers.heapy.HeapyRequestHandler]

##### Example Output
The following is a very abbreviated repport:

    {
        "rows": [
            {
                "count": {
                    "percent": 40,
                    "value": 45068
                },
                "cumulative": {
                    "percent": 29,
                    "value": 4159016
                },
                "item": "types.CodeType",
                "referrers": {
                    "rows": [
                        {
                            "count": {
                                "percent": 96,
                                "value": 7290
                            },
                            "cumulative": {
                                "percent": 96,
                                "value": 874800
                            },
                            "item": "function",
                            "size": {
                                "percent": 96,
                                "value": 874800
                            }
                        }
                    ],
                    "title": "Referrers by Kind (class / dict of class)",
                    "total_bytes": 911160,
                    "total_objects": 7593
                },
                "size": {
                    "percent": 29,
                    "value": 4159016
                }
            }
        ],
        "title": "Referrers by Kind (class / dict of class)",
        "total_bytes": 14584240,
        "total_objects": 113444
    }


### Configuration

#### Application Options
The following are the keys that are available to be used for your Tinman/Tornado application.
- cookie_secret: A salt for signing cookies when using secure cookies
- debug: Toggle tornado.Application's debug mode
- login_url: Login URL when using Tornado's @authenticated decorator
- paths:
   - base: The root of the files for the application
   - static: The path to static files
   - templates: The path to template files
   - translations: The path to translation files
- redis: If using tinman.handlers.redis.RedisRequestHandler to auto-connect to redis.
  - host: The redis server IP address
  - port: The port number
  - db: The database number
- rabbitmq:
  - host: the hostname
  - port: the server port
  - virtual_host: the virtual host
  - username: the username
  - password: the password
- session: Configuration if using tinman.handlers.session.SessionRequestHandler
  - adapter:
    - class: The classname for the adapter. One of FileSessionAdapter, RedisSessionAdapter
    - configuration: SessionAdapter specific configuration
  - cookie:
    - name: The cookie name for the session ID
  - duration: The duration in seconds for the session lifetime
- template_loader: The python module.Class to override the default template loader with
- transforms: A list of transformation objects to add to the application in module.Class format
- ui_modules: Module for the UI modules classes, can be a single module, a mapping of
              modules (dict) or a list of modules.
- xsrf_cookies: Enable xsrf_cookie mode for forms
- whitelist: List of IP addresses in CIDR notation if whitelist decorator is to be used

##### Notes
The tinman-init script will create a skeleton Tinman directory structure for
your project and create a setup.py that will put the static and template files
in /usr/share/<project-name>.

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

But is able to do a minimal logging config thanks to clihelper defaults. The following is the minimal logging configuration required:

    Logging:
        tinman:
          handlers: [console]
          propagate: True
          formatter: verbose
          level: DEBUG
        tornado:
          handlers: [console]
          propagate: True
          formatter: verbose
          level: INFO


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
The following is a "full" example tinman application configuration:

    %YAML 1.2
    ---
    Application:
      path:
        base: /home/foo/mywebsite
      debug: True
      xsrf_cookies: False
      wake_interval: 60
      # Any other vaidate Tornado application setting item

    Daemon:
      pidfile: /tmp/myapp.pid
      user: www-data
      group: www-data

    HTTPServer:
      no_keep_alive: False
      ports: [8000,8001]
      xheaders: True

    Logging:
      version: 1
      formatters:
        verbose:
          format: '%(levelname) -10s %(asctime)s %(process)-6d %(processName) -20s %(name) -20s %(funcName) -25s: %(message)s'
          datefmt: '%Y-%m-%d %H:%M:%S'
        syslog:
          format: ' %(levelname)s <PID %(process)d:%(processName)s> %(name)s.%(funcName)s(): %(message)s'
      handlers:
        console:
          class: logging.StreamHandler
          debug_only: True
          formatter: verbose
        error:
          filename: /Users/gmr/Source/Tinman/logs/error.log
          class: logging.handlers.RotatingFileHandler
          maxBytes: 104857600
          backupCount: 6
          formatter: verbose
        file:
          filename: /Users/gmr/Source/Tinman/logs/tinman.log
          class: logging.handlers.RotatingFileHandler
          maxBytes: 104857600
          backupCount: 6
          formatter: verbose
        syslog:
          class: logging.handlers.SysLogHandler
          facility: local6
          address: /var/run/syslog
          formatter: syslog
      loggers:
        clihelper:
          handlers: [console]
          level: DEBUG
          propagate: True
          formatter: verbose
        tinman:
          handlers: [console, file]
          propagate: True
          formatter: verbose
          level: DEBUG
        tornado:
          handlers: [console, file]
          propagate: True
          formatter: verbose
          level: INFO
      root:
        handlers: [error]
        formatter: verbose
        level: ERROR
      disable_existing_loggers: True

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

    from tinman.decorators import whitelist
    from tornado import web

    # Define the whitelist as part of your application settings
    settings['whitelist'] = ['10.0.0.0/8',
                             '192.168.1.0/24',
                             '1.2.3.4/32']

    application = Application(routes, **settings)

    # Specify the decorator in each method of your RequestHandler class
    # where you'd like to enforce the whitelist
    class MyClass(web.RequestHandler):

      @whitelist.Whitelisted
      def get(self):
          self.write("IP was whitelisted")

In addition you may add the whitelist right into the configuration file:

    Application:
      whitelist:
        - 10.0.0.0/8
        - 192.168.1.0/24
        - 1.2.3.4/32

### tinman.decorators.memoize
A local in-memory cache decorator. RequestHandler class method calls are cached
by name and arguments. Note that this monkey-patches the RequestHandler class
on execution and will cache the total output created including all of the
template rendering if there is anything. Local cache can be flushed with
_tinman.decorators.memoize.flush()

#### Example

    from tornado import web
    from tinman.decorators import whitelist

    class MyClass(web.RequestHandler):

       @tinman.memoize
       def get(self, content_id):
           self.write("Hello, World")

## Modules

### CouchDB Loader

Tinman includes tinman.loaders.couchdb.CouchDBLoader to enable the storage of
templates in CouchDB to provide a common stemplate storage mechanism across
multiple servers.

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
