"""Custom Tinman Handlers add wrappers to based functionality to speed
application development.

"""
HEAD = 'HEAD'
GET = 'GET'
POST = 'POST'
DELETE = 'DELETE'
PATCH = 'PATCH'
PUT = 'PUT'
OPTIONS = 'OPTIONS'

from tinman.handlers.base import RequestHandler
from tinman.handlers.session import SessionRequestHandler
