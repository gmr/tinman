#!/usr/bin/env python
"""
Tinman Request Handler

"""

__author__  = "Gavin M. Roy"
__email__   = "gavinmroy@gmail.com"
__date__    = "2009-11-10"
__version__ = 0.3

import httplib
import logging
import tinman.cache
import tinman.data
import tinman.session
import tornado.locale
import tornado.web

cache = None

class ErrorHandler(tornado.web.RequestHandler):

    """
    Default Error Handler for 404 Errors
    """

    def get(self):
        return self.render('templates/error.html',
                            host=self.request.host,
                            status_code=404,
                            message=httplib.responses[404] );

class RequestHandler(tornado.web.RequestHandler):

    def __init__(self, application, request, transforms=None):

        global cache

        # Init the parent class
        super( RequestHandler, self ).__init__(application, request, transforms)

        logging.debug('New Instance of %s' % self.__class__.__name__)

        # Create a new instance of the data layer
        if application.settings.has_key('Data'):
            self.data = tinman.data.DataLayer(application.settings['Data'])

        # Connect to the caching layer
        if application.settings.has_key('Memcache'):
            if not cache:
                logging.info('Creating a new cache client for RequestHandler')
                cache = tinman.cache.Cache(application.settings['Memcache'])

            # Assign the global cache handle to this object
            self.cache = cache

        # Create a new instance of the session handler
        if application.settings.has_key('Session'):
            logging.debug("Loading Session")
            self.session = tinman.session.Session(self)

    def get_current_user(self):

        try:
            username = self.session.username
        except AttributeError:
            # The session isn't tied to a user so just return none
            return None
        
        # We have a valid user object
        return username

    def get_error_html(self, status_code):
    
        """
        Custom Error HTML Template
        """
        return self.render('templates/error.html',
                           host=self.request.host,
                           status_code=status_code,
                           message=httplib.responses[status_code] );

    def get_user_locale(self):

        # Try and get it from the arguments
        in_session = False
        locale = self.get_argument('locale', None)

        # Did we not override it? Check our session
        if not locale:
            if self.session.values.has_key("locale"):
                locale = self.session.locale
                in_session = True

        # We don't have a locale yet, get the browser's accept language
        if not locale and self.request.headers.has_key('Accept-Language'):
            temp = self.request.headers['Accept-Language']
            parts = temp.split(';')
            if parts[0].find(','):
                parts = parts[0].split(',')
            locale = parts[0]

        # If there is a locale
        if locale:

            # Get the supported locale list
            supported_locales = tornado.locale.get_supported_locales(locale)
    
            # If our locale is supported return it
            if locale in supported_locales:
                if not in_session:
                    self.session.locale = locale
                    self.session.save()
                return tornado.locale.get(locale)

        # There is no supported locale
        return None
        
    def __del__(self):
      
        if self.cache:
            del(self.cache)