"""
Tinman Test Application

"""
import logging
from tornado import web

from tinman.handlers import SessionRequestHandler
from tinman import __version__

LOGGER = logging.getLogger(__name__)


CONFIG = {'Application': {'debug': True,
                          'xsrf_cookies': False},
          'HTTPServer': {'no_keep_alive': False,
                         'ports': [8000],
                         'xheaders': False},
          'Logging': {'loggers': {'tinman': {'propagate': True,
                                            'level': 'DEBUG'}},
                      'formatters': {'verbose': ('%(levelname) -10s %(asctime)s'
                                                 ' %(name) -30s %(funcName) '
                                                 '-25s: %(message)s')},
                      'filters': {'tinman': 'tinman'},
                      'handlers': {'console': {'formatter': 'verbose',
                                               'filters': ['tinman'],
                                               'debug_only': True,
                                               'class': 'logging.StreamHandler',
                                               'level': 'DEBUG'},
                                   'file': {'delay': False,
                                            'mode': 'a',
                                            'encoding': 'UTF-8',
                                            'formatter': 'verbose',
                                            'filters': ['tinman'],
                                            'class': 'logging.FileHandler',
                                            'filename': '/tmp/tinman.log'}}},
          'Routes': [("/", "tinman.test.DefaultHandler")]}


class Handler(SessionRequestHandler):

    @web.asynchronous
    def get(self, *args, **kwargs):
        """Example HTTP Get response method.

        :param args: positional args
        :param kwargs: keyword args

        """
        self.session.username = 'gmr'

        session = self.session.as_dict()
        if session['last_request_at']:
            session['last_request_at'] = session['last_request_at'].isoformat()

        # Send a JSON string for our test
        self.write({'message': 'Hello World',
                    'request': {'method': self.request.method,
                                'protocol': self.request.protocol,
                                'path': self.request.path,
                                'query': self.request.query,
                                'remote_ip': self.request.remote_ip,
                                'version': self.request.version},
                    'session': session,
                    'tinman': {'version':  __version__}})
        self.finish()
