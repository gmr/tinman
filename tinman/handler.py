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

        # Init the parent class
        super( RequestHandler, self ).__init__(application, request, transforms)

        logging.debug('New Instance of %s' % self.__class__.__name__)

        # Create a new instance of the data layer
        if application.settings.has_key('Data'):
            self.data = tinman.data.DataLayer(application.settings['Data'])

        # Connect to the caching layer
        if application.settings.has_key('Memcache'):
            self.cache = tinman.cache.Cache(application.settings['Memcache'])

        # Create a new instance of the session handler
        if application.settings.has_key('Session'):
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
        # Note: Access it via self.locale property

        # Try and get it from the arguments. This is rather hackish since it
        # relies on get_user_locale being called at least once per page load.
        # However, tornado always calls this function so we are safe.. for now.
        locale = self.get_argument('setLanguage', None)

        # Get the supported locale list
        supported_locales = tornado.locale.get_supported_locales(None)

        # Did we not override it? Check our session
        if not locale or locale not in supported_locales:
            if self.session.values.has_key('locale'):
                locale = self.session.locale
                if locale in supported_locales:
                    return tornado.locale.get(locale)

        # We don't have a locale yet, get the browser's accept-language header
        if not locale and self.request.headers.has_key('Accept-Language'):
            header = self.request.headers['Accept-Language']
            langs = [v for v in header.split(',') if v]
            qs = []
            for lang in langs:
                pieces = lang.split(';')
                lang, params = pieces[0].strip().lower(), pieces[1:]
                q = 1
                for param in params:
                    if '=' not in param:
                        # Malformed request; probably a bot, we'll ignore
                        continue
                    lvalue, rvalue = param.split('=')
                    lvalue = lvalue.strip().lower()
                    rvalue = rvalue.strip()
                    if lvalue == 'q':
                        q = float(rvalue)
                qs.append((lang, q))
            qs.sort(lambda a, b: -cmp(a[1], b[1]))

            # Loop over locales to take the first one which is supported
            for (lang, q) in qs:
                lang_cc = lang = lang.replace('-', '_').lower()
                if '_' in lang:
                    lang_cc = lang.split('_')[0]

                # Loop over supported locales and see if there's something matching
                for loc in supported_locales:
                    # Exact match -> this is our locale
                    if loc.lower() == lang or loc.lower() == lang_cc:
                        print 'Exact match: %s' % loc
                        locale = loc
                        break
                    # If we have a 'en_US'-style locale, try comparing only the first part
                    if '_' in loc:
                        loc_cc = loc.split('_')[0].lower()
                        if loc_cc == lang_cc:
                            print 'CC match: %s' % loc_cc
                            locale = loc
                            break

                # We found a locale; no need to try the other accepted languages
                if locale:
                    break


        # If we have no valid locale yet, use the default
        if not locale or locale not in supported_locales:
            locale = 'en_US'

        # Update session
        self.session.locale = locale
        self.session.save()
        return tornado.locale.get(locale)
