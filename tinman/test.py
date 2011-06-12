"""
Module document
"""
__author__ = 'gmr'
__since__ = '6/6/11'

import logging
import tinman
from tornado import web

CONFIG = {'Application': {'debug': True,
                          'xsrf_cookies': False},
         'HTTPServer': {'no_keep_alive': False,
                        'ports': [8000],
                        'xheaders': False},
         'Logging': {'filename': 'log.txt',
                     'format': "%(module)-12s# %(lineno)-5d %(levelname) -10s\
%(asctime)s  %(message)s",
                     'level': logging.DEBUG},
         'Routes': [("/", "tinman.test.DefaultHandler")]}


class DefaultHandler(web.RequestHandler):

    def get(self):

        # Send a JSON string for our test
        self.write({"message": "Hello World",
                    "request": {"method": self.request.method,
                                "protocol": self.request.protocol,
                                "path": self.request.path,
                                "query": self.request.query,
                                "remote_ip": self.request.remote_ip,
                                "version": self.request.version},
                    "tinman": {"version":  "%i.%i.%i" % tinman.__version__}})
