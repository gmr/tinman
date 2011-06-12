"""
Main Tinman Application Class
"""
__author__ = 'gmr'
__since__ = '6/6/11'

# Import our version number
from . import utils
from . import __version__

import logging
import os

from tornado import web

class TinmanApplication(web.Application):

    def __init__(self, routes=None, **settings):

        # Define our logger
        self._logger = logging.getLogger('tinman')

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

            # Set the app version from the version setting in this file
            if 'version' not in settings:
                settings['version'] = "%i.%i.%i" % __version__

            # Set the base path for use inside the app since all code locations
            # are not relative
            if 'base_path' not in settings:
                settings['base_path'] = \
                    os.path.dirname(os.path.realpath(__file__))

            # If we have a static_path
            if 'static_path' in settings:
                # Replace __base_path__ with the path this is running from
                settings['static_path'] =\
                    settings['static_path'].replace('__base_path__',
                                                    settings['base_path'])

        if settings.get('route_decorator', None):
            # @TODO make this work with a route decorator
            del settings['route_decorator']
            raise AttributeError("No defined routes")

        # If we specified the UI modules module we need to import it
        if 'ui_modules' in settings:
            try:
                # Assign the modules to the import
                settings['ui_modules'] = \
                    utils.import_namespaced_class(settings['ui_modules'])
            except ImportError as err:
                self._logger.error("Error importing UI Modules %s: %s",
                                   settings['ui_modules'], err)

        # Create our Application for this process
        web.Application.__init__(self, prepared_routes, **settings)

    def _prepare_route(self, attributes):
        """Take a given inbound list for a route and parse it creating the
        route and importing the class it belongs to.

        :param route: Route attributes
        :type route: list or tuple
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
            route =r"%s" % attributes[1]
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
        except ImportError as err:
            self._logger.error("Module import error for %s: %r",
                               module, err)
            return None

        # Our base prepared route
        prepared_route = [route, handler]

        # If the route has an optional kwargs dict
        if kwargs:
            prepared_route.append(kwargs)

        # Return the route
        return tuple(prepared_route)
