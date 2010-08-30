#!/usr/bin/env python
"""
Tinman Session Handler
"""

__author__  = "Gavin M. Roy"
__email__   = "gavinmroy@gmail.com"
__date__    = "2010-03-09"
__version__ = 0.1

import datetime
import hashlib
import logging
import os
import pickle

# Global Cache handle
cache = None

class Cleanup:
    """ File Based Session Cleanup Class """

    def __init__(self, settings, base_path):

        # If our storage type is file, set the base path for the session file
        if settings['type'] == 'file':
            self.path = settings['directory'].replace('__base_path__', base_path)

        # Get the number of seconds that must be exceeded for a stale connection
        self.max_age = 86400 * settings['duration']

    def process(self):
        import time
        logging.info('Processing %s for stale session files older than %i seconds' % (self.path, self.max_age))
        for root, dirs, files in os.walk(self.path):
            for file in files:
                path = '/'.join([self.path, file])
                stat = os.stat(path)
                min_age = time.mktime(datetime.datetime.now().timetuple()) - self.max_age
                if stat.st_mtime < min_age:
                    age = time.mktime(datetime.datetime.now().timetuple()) - stat.st_mtime
                    logging.info('Removing %s, last updated %i seconds ago' %
                                 (file, age))
                    os.unlink(path)

class Session:

    # List of attributes to not store in session dictionary
    protected = ['id', 'cache', 'handler', 'path', 'protected', 'settings', 'values']

    # Empty session dictionary
    values = {}

    def __init__(self, handler):
        global cache

        logging.debug('Session object initialized')

        # Carry the handler object for access to settings and cookies
        self.handler = handler

        # Make sure there are session settings
        if handler.application.settings.has_key('Session'):
            self.settings = handler.application.settings['Session']
        else:
            raise Exception('Application settings are missing the Session entries')

        # If our storage type is file, set the base path for the session file
        if self.settings['type'] == 'file':
            self.path = self.settings['directory'].replace('__base_path__',
                                                           handler.application.settings['base_path'])
        elif self.settings['type'] == 'memcache':
            import tinman.cache

            # If the cache object isn't set yet
            if not cache:
                cache = tinman.cache.Cache(self.settings)

            # A handle for our object
            self.cache = cache

        else:
            logging.error("Unknown session handler type: %s" % self.settings['type'])

        # Try and get the current session
        self.id = self.handler.get_secure_cookie(self.settings['cookie_name'])

        # If we have one, try and load the values, otherwise start a new session
        if self.id:
            self._load()
        else:
            self.id = self._new()

            # Save the initial session
            self.save()

    def __delattr__(self, key):

        # If our key is not in our protected list, try and remove it from the session dict
        if key not in self.protected:
            logging.debug('Removing "%s" from the session dictionary' % key)
            if self.values.has_key(key):
                del(self.values[key])
        else:
            # For some reason we want to remove this, so allow it
            del(self.__dict__[key])

    def __setattr__(self, key, value):

        # If our key is not in our protected list, try and remove it from the session dict
        if key not in self.protected:
            logging.debug('Adding "%s" to the session dictionary' % key)
            self.values[key] = value
        else:
            # Set the attribute in the object dict
            self.__dict__[key] = value

    def __getattr__(self, key, type=None):

        if key not in self.protected:
            if self.values.has_key(key):
                return self.values[key]
        else:
            return self.__dict__[key]
        return None

    def _load(self):

        # If we're storing using files
        if self.settings['type'] == 'file':

            # Create the full path to the session file
            session_file = '/'.join([self.path, self.id])
            logging.debug('Loading contents of session file: %s' % session_file)
            try:
                with open(session_file, 'r') as f:
                    self.values = pickle.loads(f.read())
                f.closed
            except IOError:
                logging.info('Missing session file for session %s, creating new with same id' % self.id)

                # Set the session start time
                self.started = datetime.datetime.now()

                # Save the initial session
                self.save()
        elif self.settings['type'] == 'memcache':

            # Get our values from memcache
            self.values = self.cache.get(self.id)

    def _new(self):
        """ Create a new session ID and set the session cookie """

        if not self.handler.request.headers.has_key('User-Agent'):
            self.handler.request.headers['User-Agent'] = 'Not Set'

        # Create a string we can hash that should be fairly unique to the request
        s = ':'.join([self.handler.request.remote_ip,
                      self.handler.request.headers['User-Agent'],
                      str(datetime.datetime.today())])

        # Build the sha1 based session id
        h = hashlib.sha1()
        h.update(s)
        id = h.hexdigest()

        # Send the cookie
        self.handler.set_secure_cookie( self.settings['cookie_name'],
                                        id,
                                        self.settings['duration'])

        # Set the session start time
        self.started = datetime.datetime.now()

        # Return the session id
        return id

    def clear(self):

        # Clear the session cookie
        self.handler.clear_cookie(self.settings['cookie_name'])

        # If we're storing with files
        if self.settings['type'] == 'file':

            # Create the full path to the session file
            session_file = '/'.join([self.path, self.id])
            logging.debug('Removing cleared session file: %s' % session_file)

            # Unlink the file
            os.unlink(session_file)

        elif self.settings['type'] == 'memcache':
            self.cache.delete(self.id)

        # Remove the id
        del(self.id)

    def save(self):

        # If we're storing using files
        if self.settings['type'] == 'file':

            # Create the full path to the session file
            session_file = '/'.join([self.path, self.id])
            logging.debug('Writing contents of session file: %s' % session_file)
            try:
                with open(session_file, 'w') as f:
                    f.write(pickle.dumps(self.values))
                f.closed
            except IOError:
                logging.error('Could not write to session file: %s' % session_file)

        elif self.settings['type'] == 'memcache':
            self.cache.set(self.id, self.values, self.settings['duration'] * 86400)

if __name__ == "__main__":

    import optparse
    import sys
    import yaml

    usage = "usage: session.py -c <configfile>"
    version_string = "session.py %s" % __version__
    description = "Run cleanup of stale session files when using file based session storage."

    # Create our parser and setup our command line options
    parser = optparse.OptionParser(usage=usage,
                         version=version_string,
                         description=description)

    parser.add_option("-p", "--path",
                        action="store", dest="path",
                        help="Base path for Tinman install")
    parser.add_option("-c", "--config",
                        action="store", dest="config",
                        help="Specify the configuration file for use")

    # Parse our options and arguments
    options, args = parser.parse_args()

    if options.config is None:
        sys.stderr.write('Missing configuration file\n')
        print usage
        sys.exit(1)

    if options.path is None:
        sys.stderr.write('You must specify the base path for your Tinman install\n')
        print usage
        sys.exit(1)

    # try to load the config file.
    try:
        stream = file(options.config, 'r')
        config = yaml.load(stream)
        stream.close()
    except IOError, err:
        sys.stderr.write('Configuration file not found "%s"\n' % options.config)
        sys.exit(1)
    except yaml.scanner.ScannerError, err:
        sys.stderr.write('Invalid configuration file "%s":\n%s\n' % (options.config, err))
        sys.exit(1)

    # Set the logging level to debug
    settings = {'level': logging.DEBUG}
    logging.basicConfig(**settings)

    logging.info('Tinman session file cleanup running')

    cleanup = Cleanup(config['Application']['Session'], options.path)
    cleanup.process()
