"""
Base Tinman RequestHandlers

"""
import datetime
from tornado import gen
import json
import logging
from tornado import escape
from tornado import web

from tinman import config
from tinman import session

LOGGER = logging.getLogger(__name__)

HEAD = 'HEAD'
GET = 'GET'
POST = 'POST'
DELETE = 'DELETE'
PATCH = 'PATCH'
PUT = 'PUT'
OPTIONS = 'OPTIONS'


class RequestHandler(web.RequestHandler):
    """A base RequestHandler that adds the following functionality:

    - If sending a dict, checks the user-agent string for curl and sends an
      indented, sorted human-readable JSON snippet
    - Toggles the ensure_ascii flag in json.dumps
    - Overrides the default behavior for unimplemented methods to instead set
    the status and look to the allow object attribute for methods that can be
    allowed. This is useful for when using NewRelic since the newrelic agent
    will catch the normal exceptions thrown as errors and trigger false alerts.

    To use, do something like::

        from tinman import handlers

        class Handler(handlers.RequestHandler):

            ALLOW = [handlers.GET, handlers.POST]

            def get(self, *args, **kwargs):
                self.write({'foo': 'bar'})

            def post(self, *args, **kwargs):
                self.write({'message': 'Saved'})

    """
    ALLOW = []
    JSON = 'application/json'

    def __init__(self, application, request, **kwargs):
        super(RequestHandler, self).__init__(application, request, **kwargs)

    def _method_not_allowed(self):
        self.set_header('Allow', ', '.join(self.ALLOW))
        self.set_status(405, 'Method Not Allowed')
        self.finish()

    @web.asynchronous
    def head(self, *args, **kwargs):
        """Implement the HTTP HEAD method

        :param list args: Positional arguments
        :param dict kwargs: Keyword arguments

        """
        self._method_not_allowed()

    @web.asynchronous
    def get(self, *args, **kwargs):
        """Implement the HTTP GET method

        :param list args: Positional arguments
        :param dict kwargs: Keyword arguments

        """
        self._method_not_allowed()

    @web.asynchronous
    def post(self, *args, **kwargs):
        """Implement the HTTP POST method

        :param list args: Positional arguments
        :param dict kwargs: Keyword arguments

        """
        self._method_not_allowed()

    @web.asynchronous
    def delete(self, *args, **kwargs):
        """Implement the HTTP DELETE method

        :param list args: Positional arguments
        :param dict kwargs: Keyword arguments

        """
        self._method_not_allowed()

    @web.asynchronous
    def patch(self, *args, **kwargs):
        """Implement the HTTP PATCH method

        :param list args: Positional arguments
        :param dict kwargs: Keyword arguments

        """
        self._method_not_allowed()

    @web.asynchronous
    def put(self, *args, **kwargs):
        """Implement the HTTP PUT method

        :param list args: Positional arguments
        :param dict kwargs: Keyword arguments

        """
        self._method_not_allowed()

    @web.asynchronous
    def options(self, *args, **kwargs):
        """Implement the HTTP OPTIONS method

        :param list args: Positional arguments
        :param dict kwargs: Keyword arguments

        """
        self.set_header('Allow', ', '.join(self.ALLOW))
        self.set_status(204)
        self.finish()

    def prepare(self):
        """Prepare the incoming request, checking to see the request is sending
        JSON content in the request body. If so, the content is decoded and
        assigned to the json_arguments attribute.

        """
        super(RequestHandler, self).prepare()
        self.json_arguments = None
        if self.request.headers.get('content-type', '').startswith(self.JSON):
            self.json_arguments = escape.json_decode(self.request.body)

    def write(self, chunk):
        """Writes the given chunk to the output buffer. Checks for curl in the
        user-agent and if set, provides indented output if returning JSON.

        To write the output to the network, use the flush() method below.

        If the given chunk is a dictionary, we write it as JSON and set
        the Content-Type of the response to be ``application/json``.
        (if you want to send JSON as a different ``Content-Type``, call
        set_header *after* calling write()).

        :param mixed chunk: The string or dict to write to the client

        """
        if self._finished:
            raise RuntimeError("Cannot write() after finish().  May be caused "
                               "by using async operations without the "
                               "@asynchronous decorator.")
        if isinstance(chunk, dict):
            options = {'ensure_ascii': False}
            if 'curl' in self.request.headers.get('user-agent'):
                options['indent'] = 2
                options['sort_keys'] = True
            chunk = json.dumps(chunk, **options).replace("</", "<\\/") + '\n'
            self.set_header("Content-Type", "application/json; charset=UTF-8")
        self._write_buffer.append(web.utf8(chunk))



class SessionRequestHandler(RequestHandler):
    """A RequestHandler that adds session support. For configuration details
    see the tinman.session module.

    """
    SESSION_COOKIE_NAME = 'session'
    SESSION_DURATION = 3600

    @gen.coroutine
    def on_finish(self):
        """Called by Tornado when the request is done. Update the session data
        and remove the session object.

        """
        self.session.last_request_at = datetime.datetime.now().strftime('%s')
        self.session.last_request_uri = self.request.uri
        yield self.session.save()
        del self.session
        super(SessionRequestHandler, self).on_finish()

    @gen.coroutine
    def prepare(self):
        """Prepare the session, setting up the session object and loading in
        the values, assigning the IP address to the session if it's an new one.

        """
        super(SessionRequestHandler, self).prepare()
        self.session = self._session_start()

        # Attempt to load the session data in
        result = yield self.session.fetch()
        if not self.session.get('ip_address'):
            self.session.ip_address = self.request.remote_ip
        self._last_values()
        self._set_session_cookie()
        LOGGER.debug('Session ID: %s', self.session.id)

    @property
    def _cookie_expiration(self):
        """Return the expiration timestamp for the session cookie.

        :rtype: datetime

        """
        value = (datetime.datetime.utcnow() +
                 datetime.timedelta(seconds=self._session_duration))
        LOGGER.debug('Cookie expires: %s', value.isoformat())
        return value

    @property
    def _cookie_settings(self):
        return self.settings['session'].get('cookie', dict())

    def _last_values(self):
        """Always carry last_request_uri and last_request_at even if the last_*
        values are null.

        """
        if not self.session.get('last_request_uri'):
            self.session.last_request_uri = None
        lra = float(self.session.get('last_request_at') or 0)
        self.session.last_request_at = (datetime.datetime.fromtimestamp(lra)
                                        if lra else None)

    @property
    def _session_class(self):
        if self._session_settings.get('name') == config.FILE:
            return session.FileSession
        elif self._session_settings.get('name') == config.REDIS:
            return session.RedisSession
        else:
            raise ValueError('Unknown adapter type')

    @property
    def _session_cookie_name(self):
        """Return the session cookie name, defaulting to the class default

        :rtype: str

        """
        return self._cookie_settings.get(config.NAME, self.SESSION_COOKIE_NAME)

    @property
    def _session_duration(self):
        """Return the session duration from config or the default value

        :rtype: int

        """
        return self._cookie_settings.get(config.DURATION, self.SESSION_DURATION)

    @property
    def _session_id(self):
        """Returns the session id from the session cookie.

        :rtype: str

        """
        return self.get_secure_cookie(self._session_cookie_name, None)

    @property
    def _session_settings(self):
        return self.settings['session'].get('adapter', dict())

    def _session_start(self):
        """Return an instance of the proper session object.

        :rtype: Session

        """
        return self._session_class(self._session_id,
                                   self._session_duration,
                                   self._session_settings)
    def _set_session_cookie(self):
        """Set the session data cookie."""
        LOGGER.debug('Setting session cookie for %s', self.session.id)
        self.set_secure_cookie(name=self._session_cookie_name,
                               value=self.session.id,
                               expires=self._cookie_expiration)
