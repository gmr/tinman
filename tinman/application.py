"""
Main Tinman Application Class

"""
import logging
from os import path
import sys
from tornado import web

# Import our version number
from tinman import utils
from tinman import __version__

LOGGER = logging.getLogger(__name__)


class TinmanApplication(web.Application):
    """TinmanApplication extends web.Application and handles all sorts of things
    for you that you'd have to handle yourself.

    """
    def __init__(self, routes=None, port=None, **settings):
        """Create a new TinmanApplication instance with the specified Routes and
        settings.

        :param list routes: A list of route tuples
        :param int port: The port number for the HTTP server
        :param dict settings: Application settings

        """
        # Assign the settings
        self._settings = settings or dict()

        # If we have a base path, add it to our sys path
        if 'base_path' in settings:
            sys.path.insert(0, settings['base_path'])

        # Create a TinmanAttributes for assignments to application scope
        self.tinman = TinmanAttributes()

        # A handle for a HTTP Port we may want to use when logging
        self.port = port

        # Prepare the paths
        self._prepare_paths()

        # If a translation paths is specified, load the translations
        if 'translations_path' in self._settings:
            self._load_translations(self._settings['translations_path'])

        # Set the app version from the version setting in this file
        self._prepare_version()

        # Prepare the routes
        LOGGER.debug('Routes: %r', routes)
        prepared_routes = self._prepare_routes(routes)

        # Setup the transforms
        self._prepare_transforms()

        # Setup the UI modules
        self._prepare_uimodules()

        # Create our Application for this process
        super(TinmanApplication, self).__init__(prepared_routes,
                                                **self._settings)

    def _load_translations(self, path):
        """Load the translations from the specified path.

        :param str path: The path to the translations

        """
        LOGGER.info('Loading translations from %s', path)
        from tornado import locale
        locale.load_translations(path)

    def _prepare_paths(self):
        """Setup and override the settings values for given paths by finding the
        locations of base_path if set, package location if set, etc.

        :raises: ValueError

        """
        LOGGER.debug('Preparing paths')
        # Try and load a package if specified
        package_path = None
        if 'package_name' in self._settings:
            package = None
            try:
                package = __import__(self._settings['package_name'],
                                     globals(), locals())
            except ImportError as error:
                LOGGER.error('Could not import package %s in config: %s',
                                   self._settings['package_name'], error)
            if package:
                package_path = path.abspath(path.dirname(package.__file__))

        # Create a list of variables to replace our values with
        paths = list()
        for path_name in ['static_path', 'template_path', 'translation_path']:
            if path_name in self._settings:
                paths.append(path_name)

        # If we have a package path, replace it if needed
        if package_path:
            for path_name in paths:
                self._replace_path(path_name, '__package_path__', package_path)

        # If we have a package path, replace it if needed
        if self._settings.get('base_path'):
            for path_name in paths:
                self._replace_path(path_name, '__base_path__',
                                   self._settings['base_path'])

        # Make sure we've updated the core variables as needed
        for variable in ['__base_path', '__package_path__']:
            for path_name in paths:
                if self._settings[path_name].find(variable) > -1:
                    raise ValueError('%s called for but not set', variable)

    def _replace_path(self, path_name, name, value):
        """Replace the name with the value for the given path_name name.

        :param str path_name: The path_name name
        :param str name: The string to replace in original string
        :param str value: The string value replacement value for name

        """
        # If we have a base path_name, replace it if needed
        if path_name in self._settings:
            self._settings[path_name] = self._settings[path_name].replace(name,
                                                                          value)

    def _set_path(self, path_name, path_value):
        """Set the specified path setting with the given value

        :param str path_name: The path to set
        :param str path_value: Path to set it to

        """
        self._settings[path_name] = path_value

    def _prepare_route(self, attributes):
        """Take a given inbound list for a route and parse it creating the
        route and importing the class it belongs to.

        :param list attributes: Route attributes
        :rtype: list

        """
        # Validate it's a list or set
        if type(attributes) not in (list, tuple):
            LOGGER.error("Invalid route, must be a list or tuple: %r",
                               attributes)
            return False

        # By default we do not have extra kwargs
        kwargs = None

        # If we have a regex based route, set it up with a raw string
        if attributes[0] == 're':
            route = r"%s" % attributes[1]
            module = attributes[2]
            if len(attributes) == 4:
                kwargs = attributes[3]
        else:
            route  = r"%s" % attributes[0]
            module = attributes[1]
            if len(attributes) == 3:
                kwargs = attributes[2]

        LOGGER.debug("Initializing route: %s with %s", route, module)

        # Return the reference to the python class at the end of the
        # namespace. eg foo.Baz, foo.bar.Baz
        try:
            handler = utils.import_namespaced_class(module)
        except ImportError as error:
            LOGGER.error("Module import error for %s: %r",
                               module, error)
            return None

        # Our base prepared route
        prepared_route = [route, handler]

        # If the route has an optional kwargs dict
        if kwargs:
            prepared_route.append(kwargs)

        # Return the route
        return tuple(prepared_route)

    def _prepare_routes(self, routes):
        """Prepare the routes by iterating through the list of tuples & calling
        prepare route on them.

        :param routes: Routes to prepare
        :type routes: list
        :rtype: list
        :raises: ValueError

        """
        if not isinstance(routes, list):
            raise ValueError("Routes parameter must be a list of tuples")
        LOGGER.debug('Preparing routes')

        # Our prepared_routes is what we pass in to Tornado
        prepared_routes = list()

        # Iterate through the routes
        for parts in routes:

            # Prepare the route
            route = self._prepare_route(parts)
            if route:
               # Append our prepared_routes list
                LOGGER.info('Appending handler: %r', route)
                prepared_routes.append(route)
            else:
                LOGGER.warn('Skipping route %r due to prepare error',
                                  parts)

        # Return the routes we prepared
        return prepared_routes

    def _prepare_transforms(self):
        """Prepare the UI Modules object"""
        if 'transforms' in self._settings:
            LOGGER.info('Preparing %i transform class(es) for import',
                              len(self._settings['transforms']))
            transforms = list()
            for transform in self._settings['transforms']:
                try:
                    # Assign the modules to the import
                    transforms.append(utils.import_namespaced_class(transform))
                except ImportError as error:
                    LOGGER.error("Error importing UI Modules %s: %s",
                                       self._settings['ui_modules'], error)
            self._settings['transforms'] = transforms

    def _prepare_uimodules(self):
        """Prepare the UI Modules object"""
        if 'ui_modules' in self._settings:
            LOGGER.debug('Preparing uimodules for import')
            try:
                # Assign the modules to the import
                self._settings['ui_modules'] = \
                    utils.import_namespaced_class(self._settings['ui_modules'])
            except ImportError as error:
                LOGGER.error("Error importing UI Modules %s: %s",
                                   self._settings['ui_modules'], error)

    def _prepare_version(self):
        """Setup the application version"""
        if 'version' not in self._settings:
            self._settings['version'] = __version__

    def log_request(self, handler):
        """Writes a completed HTTP request to the logs.

        By default writes to the tinman.application LOGGER.  To change
        this behavior either subclass Application and override this method,
        or pass a function in the application settings dictionary as
        'log_function'.
        """
        if "log_function" in self.settings:
            self.settings["log_function"](handler)
            return
        if handler.get_status() < 400:
            log_method = LOGGER.info
        elif handler.get_status() < 500:
            log_method = LOGGER.warning
        else:
            log_method = LOGGER.error
        request_time = 1000.0 * handler.request.request_time()
        log_method("%d %s %.2fms", handler.get_status(),
                   handler._request_summary(), request_time)


class TinmanAttributes(object):
    """A base object to hang attributes off of for application level scope that
    can be used across connections.

    """
    def __init__(self):
        self._attributes = dict()

    def __contains__(self, value):
        LOGGER.debug('Running %s against %r', value, self._attributes)
        return value in self._attributes.keys()

    def __delattr__(self, name):
        if name not in self._attributes:
            raise AttributeError('%s is not set' % name)
        if name in self._attributes:
            del self._attributes[name]

    def __getattr__(self, item):
        if item == '_attributes':
            super(TinmanAttributes, self).__getattr__(item)
        return self._attributes.get(item)

    def __setattr__(self, name, value):
        if name == '_attributes':
            super(TinmanAttributes, self).__setattr__(name, value)
        self._attributes[name] = value

    def add(self, name, value):
        """Add an attribute value to our object instance.

        :param str name: Connection attribute name
        :param any value: Value to associate with the attribute
        :raises: AttributeError

        """
        if hasattr(self, name):
            raise AttributeError('%s already exists' % name)
        setattr(self, name, value)

    def remove(self, name):
        """Remove an attribute value to our object instance.

        :param str name: Connection attribute name
        :raises: AttributeError

        """
        if not hasattr(self, name):
            raise AttributeError('%s does not exist' % name)
        delattr(self, name)
