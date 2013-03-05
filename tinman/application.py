"""
Main Tinman Application Class

"""
import logging
import sys
from tornado import web

from tinman import utils
from tinman import __version__

LOGGER = logging.getLogger(__name__)

__BASE__ = '{{base}}'
BASE = 'base'
DEFAULT_LOCALE = 'default_locale'
PATHS = 'paths'
STATIC = 'static'
TEMPLATES = 'templates'
TRANSFORMS = 'transforms'
TRANSLATIONS = 'translations'
UI_MODULES = 'ui_modules'
VERSION = 'version'


class Application(web.Application):
    """Application extends web.Application and handles all sorts of things
    for you that you'd have to handle yourself.

    """

    def __init__(self, routes=None, port=None, **settings):
        """Create a new Application instance with the specified Routes and
        settings.

        :param list routes: A list of route tuples
        :param int port: The port number for the HTTP server
        :param dict settings: Application settings

        """
        self.attributes = Attributes()
        self.port = port
        self._config = settings or dict()
        self._insert_base_path()
        self._prepare_paths()
        self._prepare_static_path()
        self._prepare_template_path()
        self._prepare_transforms()
        self._prepare_translations()
        self._prepare_uimodules()
        self._prepare_version()

        # Prepend the system path if needed
        if 'base' in self.paths:
            sys.path.insert(0, self.paths['base'])

        # Get the routes and initialize the tornado.web.Application instance
        prepared_routes = self._prepare_routes(routes)
        LOGGER.debug('Routes: %r', routes)
        super(Application, self).__init__(prepared_routes, **self._config)

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

    @property
    def paths(self):
        """Return the path configuration

        :rtype: dict

        """
        return self._config.get(PATHS, dict())

    def _import_class(self, class_path):
        """Try and import the specified namespaced class.

        :param str class_path: The full path to the class (foo.bar.Baz)
        :rtype: class

        """
        LOGGER.debug('Attempting to import %s', class_path)
        try:
            return utils.import_namespaced_class(class_path)
        except ImportError as error:
            LOGGER.critical('Could not import %s: %s', class_path, error)
            return None

    def _import_module(self, module_path):
        """Dynamically import a module returning a handle to it.

        :param str module_path: The module path
        :rtype:

        """
        LOGGER.debug('Attempting to import %s', module_path)
        try:
            return __import__(module_path)
        except ImportError as error:
            LOGGER.critical('Could not import %s: %s', module_path, error)
            return None

    def _insert_base_path(self):
        """If the "base" path is set in the paths section of the config, insert
        it into the python path.

        """
        if BASE in self.paths:
            sys.path.insert(0, self.paths[BASE])

    def _prepare_paths(self):
        """Set the value of {{base}} in paths if the base path is set in the
        configuration.

        :raises: ValueError

        """
        LOGGER.debug('Preparing paths')
        if BASE in self.paths:
            for path_name in self.paths:
                if path_name != BASE:
                    self._replace_path(path_name, __BASE__, self.paths[BASE])
            LOGGER.debug('Prepared paths: %r', self.paths)

    def _prepare_route(self, attrs):
        """Take a given inbound list for a route and parse it creating the
        route and importing the class it belongs to.

        :param list attrs: Route attributes
        :rtype: list

        """
        if type(attrs) not in (list, tuple):
            LOGGER.error('Invalid route, must be a list or tuple: %r', attrs)
            return

        # By default there are not any extra kwargs
        kwargs = None

        # If there is a regex based route, set it up with a raw string
        if attrs[0] == 're':
            route = r'%s' % attrs[1]
            classpath = attrs[2]
            if len(attrs) == 4:
                kwargs = attrs[3]
        else:
            route = r'%s' % attrs[0]
            classpath = attrs[1]
            if len(attrs) == 3:
                kwargs = attrs[2]

        LOGGER.debug('Initializing route: %s with %s', route, classpath)
        try:
            handler = self._import_class(classpath)
        except ImportError as error:
            LOGGER.error('Class import error for %s: %r', classpath, error)
            return None

        # Setup the prepared route, adding kwargs if there are any
        prepared_route = [route, handler]
        if kwargs:
            prepared_route.append(kwargs)

        # Return the prepared route as a tuple
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
            raise ValueError('Routes parameter must be a list of tuples')
        LOGGER.debug('Preparing routes')
        prepared_routes = list()
        for parts in routes:
            route = self._prepare_route(parts)
            if route:
                LOGGER.info('Appending handler: %r', route)
                prepared_routes.append(route)
        return prepared_routes

    def _prepare_static_path(self):
        if STATIC in self.paths:
            self._config['static_path'] = self.paths[STATIC]

    def _prepare_template_path(self):
        if TEMPLATES in self.paths:
            self._config['template_path'] = self.paths[TEMPLATES]

    def _prepare_transforms(self):
        """Prepare the list of transforming objects"""
        if TRANSFORMS in self._config:
            LOGGER.info('Preparing %i transform class(es) for import',
                        len(self._config[TRANSFORMS]))
            for transform in [self._import_module(transform) for transform in
                              self._config[TRANSFORMS]]:
                LOGGER.debug('Adding transform: %r', transform)
                self.add_transform(transform)

    def _prepare_translations(self):
        """Load in translations if they are set, and add the default locale as
        well.

        """
        if TRANSLATIONS in self.paths:
            LOGGER.info('Loading translations from %s',
                        self.paths[TRANSLATIONS])
            from tornado import locale
            locale.load_translations(self.paths[TRANSLATIONS])
            if DEFAULT_LOCALE in self._config:
                LOGGER.info('Setting default locale to %s',
                            self._config[DEFAULT_LOCALE])
                locale.set_default_locale(self._config[DEFAULT_LOCALE])

    def _prepare_uimodule(self):
        self._config[UI_MODULES] = self._import_module(self._config[UI_MODULES])

    def _prepare_uimodule_dict(self):
        for key, value in self._config[UI_MODULES].items():
            self._config[UI_MODULES][key] = self._import_module(value)

    def _prepare_uimodule_list(self):
        for offset, value in enumerate(self._config[UI_MODULES]):
            self._config[UI_MODULES][offset] = self._import_module(value)

    def _prepare_uimodules(self):
        """Prepare the UI Modules object, handling the three cases that Tornado
        supports for the ui_modules configuration: a single module, a mapping
        of modules in a dictionary or a list of modules.

        """
        if UI_MODULES in self._config:
            if isinstance(self._config[UI_MODULES], str):
                self._prepare_uimodule()
            elif isinstance(self._config[UI_MODULES], dict()):
                self._prepare_uimodule_dict()
            elif isinstance(self._config[UI_MODULES], list):
                self._prepare_uimodule_list()
            else:
                LOGGER.critical('Unknown format for %s configuration: %s',
                                UI_MODULES, type(self._config[UI_MODULES]))

    def _prepare_version(self):
        """Setup the application version"""
        if VERSION not in self._config:
            self._config[VERSION] = __version__

    def _replace_path(self, path_name, name, value):
        """Replace the name with the value for the given path_name name.

        :param str path_name: The path_name name
        :param str name: The string to replace in original string
        :param str value: The string value replacement value for name

        """
        if path_name in self.paths:
            self.paths[path_name] = self.paths[path_name].replace(name, value)


class Attributes(object):
    """A base object to hang attributes off of for application level scope that
    can be used across connections.

    """
    ATTRIBUTES = '_attributes'

    def __init__(self):
        """Create a new instance of the Attributes class"""
        self._attributes = dict()

    def __contains__(self, item):
        """Check to see if an attribute is set on the object.

        :param str item: The attribute name
        :rtype: bool

        """
        return item in self.__dict__[self.ATTRIBUTES].keys()

    def __delattr__(self, item):
        """Delete an attribute from the object.

        :param str item: The attribute name
        :raises: AttributeError

        """
        if item == self.ATTRIBUTES:
            raise AttributeError('Can not delete %s', item)
        if item not in self.__dict__[self.ATTRIBUTES]:
            raise AttributeError('%s is not set' % item)
        del self.__dict__[self.ATTRIBUTES][item]

    def __getattr__(self, item):
        """Get an attribute from the class.

        :param str item: The attribute name
        :rtype: any

        """
        if item == self.ATTRIBUTES:
            return self.__dict__[item]
        return self.__dict__[self.ATTRIBUTES].get(item)


    def __iter__(self):
        """Iterate through the keys in the data dictionary.

        :rtype: list

        """
        return iter(self.__dict__[self.ATTRIBUTES])

    def __len__(self):
        """Return the length of the data dictionary.

        :rtype: int

        """
        return len(self.__dict__[self.ATTRIBUTES])

    def __repr__(self):
        """Return the representation of the class as a string.

        :rtype: str

        """
        return '<%s(%r)>' % (self.__class__.__name__,
                             self.__dict__[self.ATTRIBUTES])

    def __setattr__(self, item, value):
        """Set an attribute on the object.

        :param str item: The attribute name
        :param any value: The attribute value

        """
        if item == self.ATTRIBUTES:
            self.__dict__[item] = value
        else:
            self.__dict__[self.ATTRIBUTES][item] = value

    def add(self, item, value):
        """Add an attribute value to our object instance.

        :param str item: Application attribute name
        :param any value: Value to associate with the attribute
        :raises: AttributeError

        """
        if item in self.__dict__[self.ATTRIBUTES].keys():
            raise AttributeError('%s already exists' % item)
        setattr(self, item, value)

    def remove(self, item):
        """Remove an attribute value to our object instance.

        :param str item: Application attribute name
        :raises: AttributeError

        """
        if item not in self.__dict__[self.ATTRIBUTES].keys():
            raise AttributeError('%s does not exist' % item)
        delattr(self, item)

    def set(self, item, value):
        """Set an attribute value to our object instance.

        :param str item: Application attribute name
        :param any value: Value to associate with the attribute
        :raises: AttributeError

        """
        setattr(self, item, value)
