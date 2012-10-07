"""
The SessionRequestHandler implements a base level of session handling. See
the tinman.session package to see what types of session adapters exist.

"""
import datetime
import logging
from tornado import web

LOGGER = logging.getLogger(__name__)

from tinman import session


class SessionRequestHandler(web.RequestHandler):
    """A RequestHandler that implements user sessions.  Configuration in the
    application settings is as follows:

    Application:
      session:
        adapter:
          class: FileSessionAdapter
          configuration: SessionAdapter specific configuration
        cookie:
          name: session
        duration: 3600

    All options other than the adapter class are optional.

    """
    DEFAULT_DURATION = 3600
    DEFAULT_COOKIE_NAME = 'session'

    def _clear_session(self):
        """Clear the user's sessions, resetting the cookies and removing the
        data from redis.

        """
        LOGGER.info('Clearing session')
        self._session.delete()
        self.clear_cookie(self._session_cookie_name)

    def _get_session_id(self):
        """Gets the session id from the session cookie.

        :rtype: str

        """
        return self.get_secure_cookie(self._session_cookie_name, None)

    @property
    def _session_adapter_settings(self):
        """Return the session adapter settings

        :rtype: dict

        """
        return self._session_settings.get('adapter') or dict()

    @property
    def _session_cookie_expiration(self):
        """Return the expiration timestamp for the session cookie.

        :rtype: datetime

        """
        value = (datetime.datetime.utcnow() +
                 datetime.timedelta(seconds=self._session_duration))
        LOGGER.debug('Cookie expires: %s', value.isoformat())
        return value

    @property
    def _session_cookie_name(self):
        """Return the session cookie name, defaulting to the class default

        :rtype: str

        """
        return self._session_cookie_settings.get('name',
                                                 self.DEFAULT_COOKIE_NAME)

    @property
    def _session_cookie_settings(self):
        """Return the cookie specific session settings

        :rtype: dict

        """
        return self._session_settings.get('cookie')

    @property
    def _session_duration(self):
        """Return the session duration in seconds from the configuration,
        defaulting to the class default.

        :rtype: int

        """
        return self._session_settings.get('duration', self.DEFAULT_DURATION)

    @property
    def _session_settings(self):
        """Return the session management settings.

        :rtype: dict

        """
        return self.application.settings.get_document('session') or dict()

    def _set_session_cookie(self):
        """Set the session data cookie."""
        LOGGER.debug('Setting session cookie for %s', self._session.id)
        self.set_secure_cookie(name=self._session_cookie_name,
                               value=self._session.id,
                               expires=self._session_cookie_expiration)

    def _get_session_object(self):
        """Return an instance of the session object for the current session.
        If there is no pre-existing session, the session object will be created
        with a new session id.

        :rtype: tinman.session.SessionAdapter

        """
        return session.get_session_adapter(self._session_adapter_settings,
                                           self._get_session_id(),
                                           self._session_duration)

    def prepare(self):
        """Prepare the request, starting a session if one does not exist."""
        super(SessionRequestHandler, self).prepare()
        self._session = self._get_session_object()
        self._session.load()
        if not self._session.ip_address:
            self._session.ip_address = self.request.remote_ip
        LOGGER.debug('Session ID: %s', self._session.id)
        self._set_session_cookie()

    def on_finish(self):
        """Called by Tornado when the request is done. Save the request and
        remove the redis connection.

        """
        LOGGER.debug('Saving session')
        self._session.last_request_uri = self.request.uri
        self._session.save()
