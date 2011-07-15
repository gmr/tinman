"""
Main Tinman Application Class
"""
__author__ = 'gmr'
__since__ = '2011-06-06'

import logging
from os import path
import sys
from tornado import web

# Import our version number
from . import utils
from . import __version__


def _replace_value(original, key, value):
    """Replace the string value key with value in original

    :param original: Original string
    :type original: str
    :param key: The string to replace in original string
    :type key: str
    :param value: The string value to replace it with
    :type value: str
    :returns: str

    """
    return original.replace(key, value)


class TinmanApplication(web.Application):
    """TinmanApplication extends web.Application and handles all sorts of things
    for you that you'd have to handle yourself.

    """

    def __init__(self, routes=None, **settings):

        # Define our logger
        self._logger = logging.getLogger('tinman')

        # Assign the settings
        self._settings = settings

        # If we have a base path, add it to our sys path
        if settings.get('base_path'):
            sys.path.insert(0, settings['base_path'])

        # Create a TinmanAttributes for assignments to application scope
        self.tinman = TinmanAttributes()

        # Prepare the routes
        prepared_routes = self._prepare_routes(routes)

        # Prepare the paths
        self._prepare_paths()

        # Set the app version from the version setting in this file
        self._prepare_version()

        # Setup the UI modules
        self._prepare_uimodules()

        # Create our Application for this process
        web.Application.__init__(self, prepared_routes, **self._settings)


    def _prepare_paths(self):
        """Setup and override the settings values for given paths by finding the
        locations of base_path if set, package location if set, etc.

        :raises: ValueError

        """
        # Try and load a package if specified
        package_path = None
        if 'package_name' in self._settings:
            package = None
            try:
                package = __import__(self._settings['package_name'],
                                     globals(), locals())
            except ImportError as error:
                self._logger.error('Could not import package %s in config: %s',
                                   self._settings['package_name'], error)
            if package:
                package_path = path.abspath(path.dirname(package.__file__))

        # Create a list of variables to replace our values with
        paths = list()
        for path_name in ['static_path', 'template_path']:
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

    def _replace_path(self, path_name, key, value):
        """Replace the key with the value for the given path_name name.

        :param path_name: The path_name name
        :type path_name: str
        :param key: The string to replace in original string
        :type key: str
        :param value: The string value replacement value for key
        :type value: str

        """
        # If we have a base path_name, replace it if needed
        if self._settings[path_name]:
            self._settings[path_name] = \
                _replace_value(self._settings[path_name], key, value)

    def _set_path(self, path_name, path_value):
        """Set the specified path setting with the given value

        :param path_name: The path to set
        :type path_name: str
        :param path_value: Path to set it to
        :type path_value: str

        """
        self._settings[path_name] = path_value


    def _prepare_route(self, attributes):
        """Take a given inbound list for a route and parse it creating the
        route and importing the class it belongs to.

        :param attributes: Route attributes
        :type attributes: list or tuple
        :returns: list of prepared route
        """
        # Validate it's a list or set
        if type(attributes) not in (list, tuple):
            self._logger.error("Invalid route, must be a list or tuple: %r",
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

        logging.debug("Initializing route: %s with %s", route, module)

        # Return the reference to the python class at the end of the
        # namespace. eg foo.Baz, foo.bar.Baz
        try:
            handler = utils.import_namespaced_class(module)
        except ImportError as error:
            self._logger.error("Module import error for %s: %r",
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
        :returns: list
        :raises: ValueError

        """
        if not isinstance(routes, list):
            raise ValueError("Routes parameter must be a list of tuples")

        # Our prepared_routes is what we pass in to Tornado
        prepared_routes = list()

        # Iterate through the routes
        for parts in routes:

            # Prepare the route
            route = self._prepare_route(parts)
            if route:
               # Append our prepared_routes list
                self._logger.info('Appending handler: %r', route)
                prepared_routes.append(route)
            else:
                self._logger.warn('Skipping route %r due to prepare error',
                                  parts)

        # Return the routes we prepared
        return prepared_routes

    def _prepare_uimodules(self):
        """Prepare the UI Modules object"""
        if 'ui_modules' in self._settings:
            try:
                # Assign the modules to the import
                self._settings['ui_modules'] = \
                    utils.import_namespaced_class(self._settings['ui_modules'])
            except ImportError as error:
                self._logger.error("Error importing UI Modules %s: %s",
                                   self._settings['ui_modules'], error)

    def _prepare_version(self):
        """Setup the application version"""
        if 'version' not in self._settings:
            self._settings['version'] = __version__


class TinmanAttributes(object):
    """A base object to hang attributes off of for application level scope that
    can be used across connections.

    """

    def add(self, name, value):
        """Add an attribute value to our object instance.

        :param name: Connection attribute name
        :type name: str
        :param value: Value to associate with the attribute
        :type value: any
        :raises: AttributeError
        """

        if hasattr(self, name):
            raise AttributeError('%s already exists' % name)

        setattr(self, name, value)

    def remove(self, name):
        """Remove an attribute value to our object instance.

        :param name: Connection attribute name
        :type name: str
        :raises: AttributeError
        """

        if hasattr(self, name):
            raise AttributeError('%s already exists' % name)

        delattr(self, name)
