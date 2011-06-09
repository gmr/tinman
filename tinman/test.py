"""
Module document
"""
__author__ = 'gmr'
__since__ = '6/6/11'

import logging
from tornado import web

CONFIG = {'Application': {'debug': True,
                          'xsrf_cookies': False},
         'HTTPServer': {'no_keep_alive': False,
                        'ports': [8000],
                        'xheaders': False},
         'Logging': {'filename': 'log.txt',
                     'format': "%(module)-10s# %(lineno)-5d %(levelname) -10s\
%(asctime)s  %(message)s",
                     'level': logging.DEBUG},
         'Routes': [("/", "tinman.test.DefaultHandler")]}


class DefaultHandler(web.RequestHandler):

    def get(self):
        self.write({"msg": "Hello World"})
