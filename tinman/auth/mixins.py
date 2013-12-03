"""
GitHub Authentication and API Mixins

"""
import hashlib
import logging
from tornado import auth
from tornado import concurrent
from tornado import escape
from tornado import httpclient
from tinman import __version__ as tinman_version
from tornado import version as tornado_version

LOGGER = logging.getLogger(__name__)


class OAuth2Mixin(auth.OAuth2Mixin):
    """Base OAuth2 Mixin with a few more handy functions"""
    _ACCEPT = 'application/json'
    _USER_AGENT = 'Tinman %s/Tornado %s' % (tinman_version, tornado_version)

    _API_NAME = None

    _CLIENT_ID_SETTING = None
    _CLIENT_SECRET_SETTING = None
    _BASE_SCOPE = []

    # The state value to prevent hijacking
    state = None

    def oauth2_redirect_uri(self, callback_uri=''):
        return auth.urlparse.urljoin(self.request.full_url(), callback_uri)


    @concurrent.return_future
    def authenticate_redirect(self, callback_uri=None, cancel_uri=None,
                              extended_permissions=None, callback=None):
        """Perform the authentication redirect to GitHub


        """
        self.require_setting(self._CLIENT_ID_SETTING, self._API_NAME)

        scope = self._BASE_SCOPE
        if extended_permissions:
            scope += extended_permissions

        args = {'client_id': self.settings[self._CLIENT_ID_SETTING],
                'redirect_uri': self.oauth2_redirect_uri(callback_uri),
                'scope': ','.join(scope)}

        # If cookie_secret is set, use it for GitHub's state value
        if not self.state and 'cookie_secret' in self.settings:
            sha1 = hashlib.sha1(self.settings['cookie_secret'])
            self.state = str(sha1.hexdigest())

        # If state is set, add it to args
        if self.state:
            args['state'] = self.state

        LOGGER.info('Redirect args: %r', args)

        # Redirect the user to the proper URL
        self.redirect(self._OAUTH_AUTHORIZE_URL +
                      auth.urllib_parse.urlencode(args))
        callback()

    @auth._auth_return_future
    def get_authenticated_user(self, callback):
        """ Fetches the authenticated user

        :param method callback: The callback method to invoke

        """
        self.require_setting(self._CLIENT_ID_SETTING, self._API_NAME)
        self.require_setting(self._CLIENT_SECRET_SETTING, self._API_NAME)

        if self.state:
            if (not self.get_argument('state', None) or
                self.state != self.get_argument('state')):
                LOGGER.error('State did not match: %s != %s',
                             self.state, self.get_argument('state'))
                raise auth.AuthError('Problematic Reply from %s' %
                                     self._API_NAME)

        args = {'client_id': self.settings[self._CLIENT_ID_SETTING],
                'client_secret': self.settings[self._CLIENT_SECRET_SETTING],
                'code': self.get_argument('code'),
                'redirect_uri': self.oauth2_redirect_uri()}

        http_client = self._get_auth_http_client()
        callback = self.async_callback(self._on_access_token, callback)
        http_client.fetch(self._OAUTH_ACCESS_TOKEN_URL,
                          method='POST',
                          headers={'Accept': self._ACCEPT},
                          user_agent=self._USER_AGENT,
                          body=auth.urllib_parse.urlencode(args),
                          callback=callback)

    @staticmethod
    def _get_auth_http_client():
        """Returns the `.AsyncHTTPClient` instance to be used for auth requests.

        May be overridden by subclasses to use an HTTP client other than
        the default.
        """
        return httpclient.AsyncHTTPClient()

    def _on_access_token(self, future, response):
        """This should be extended in the child mixins"""
        raise NotImplementedError


class GithubMixin(OAuth2Mixin):
    """GitHub OAuth2 Authentication

    To authenticate with GitHub, first register your application at
    https://github.com/settings/applications/new to get the client ID and
    secret.

    """
    _API_URL = 'https://api.github.com/'
    _OAUTH_ACCESS_TOKEN_URL = 'https://github.com/login/oauth/access_token'
    _OAUTH_AUTHORIZE_URL = 'https://github.com/login/oauth/authorize?'

    _API_NAME = 'GitHub API'
    _CLIENT_ID_SETTING = 'github_client_id'
    _CLIENT_SECRET_SETTING = 'github_client_secret'
    _BASE_SCOPE = ['user:email']

    def _on_access_token(self, future, response):
        """Invoked as a callback when GitHub has returned a response to the
        access token request.

        :param method future: The callback method to pass along
        :param tornado.httpclient.HTTPResponse response: The HTTP response

        """
        content = escape.json_decode(response.body)
        if 'error' in content:
            LOGGER.error('Error fetching access token: %s', content['error'])
            future.set_exception(auth.AuthError('Github auth error: %s' %
                                                str(content['error'])))
            return
        callback = self.async_callback(self._on_github_user, future,
                                       content['access_token'])
        self.github_request('user', callback, content['access_token'])

    def _on_github_user(self, future, access_token, response):
        """Invoked as a callback when self.github_request returns the response
        to the request for user data.

        :param method future: The callback method to pass along
        :param str access_token: The access token for the user's use
        :param dict response: The HTTP response already decoded

        """
        response['access_token'] = access_token
        future.set_result(response)

    @auth._auth_return_future
    def github_request(self, path, callback, access_token=None,
                       post_args=None, **kwargs):
        """Make a request to the GitHub API, passing in the path, a callback,
        the access token, optional post arguments and keyword arguments to be
        added as values in the request body or URI

        """
        url = self._API_URL + path
        all_args = {}
        if access_token:
            all_args["access_token"] = access_token
            all_args.update(kwargs)
        if all_args:
            url += "?" + auth.urllib_parse.urlencode(all_args)
        callback = self.async_callback(self._on_github_request, callback)
        http = self._get_auth_http_client()
        if post_args is not None:
            http.fetch(url, method="POST",
                       user_agent='Tinman/Tornado',
                       body=auth.urllib_parse.urlencode(post_args),
                       callback=callback)
        else:
            http.fetch(url, user_agent='Tinman/Tornado', callback=callback)

    def _on_github_request(self, future, response):
        """Invoked as a response to the GitHub API request. Will decode the
        response and set the result for the future to return the callback or
        raise an exception

        """
        try:
            content = escape.json_decode(response.body)
        except ValueError as error:
            future.set_exception(Exception('Github error: %s' %
                                           response.body))
            return

        if 'error' in content:
            future.set_exception(Exception('Github error: %s' %
                                           str(content['error'])))
            return
        future.set_result(content)





class StackExchangeMixin(OAuth2Mixin):
    """StackExchange OAuth2 Authentication

    To authenticate with StackExchange, first register your application at
    http://stackapps.com/apps/oauth/register to get the client ID and
    secret.

    """
    _API_URL = 'https://api.stackexchange.com/2.1'
    _API_NAME = 'StackExchange API'
    _CLIENT_ID_SETTING = 'stackexchange_client_id'
    _CLIENT_SECRET_SETTING = 'stackexchange_client_secret'
    _OAUTH_ACCESS_TOKEN_URL = 'https://stackexchange.com/oauth/access_token'
    _OAUTH_AUTHORIZE_URL = 'https://stackexchange.com/oauth?'

    def _on_access_token(self, future, response):
        """Invoked as a callback when StackExchange has returned a response to
        the access token request.

        :param method future: The callback method to pass along
        :param tornado.httpclient.HTTPResponse response: The HTTP response

        """
        LOGGER.info(response.body)
        content = escape.json_decode(response.body)
        if 'error' in content:
            LOGGER.error('Error fetching access token: %s', content['error'])
            future.set_exception(auth.AuthError('StackExchange auth error: %s' %
                                                str(content['error'])))
            return
        callback = self.async_callback(self._on_stackexchange_user, future,
                                       content['access_token'])
        self.stackexchange_request('me', callback, content['access_token'])

    def _on_stackexchange_user(self, future, access_token, response):
        """Invoked as a callback when self.stackexchange_request returns the
        response to the request for user data.

        :param method future: The callback method to pass along
        :param str access_token: The access token for the user's use
        :param dict response: The HTTP response already decoded

        """
        response['access_token'] = access_token
        future.set_result(response)

    @auth._auth_return_future
    def stackexchange_request(self, path, callback, access_token=None,
                       post_args=None, **kwargs):
        """Make a request to the StackExchange API, passing in the path, a
        callback, the access token, optional post arguments and keyword
        arguments to be added as values in the request body or URI

        """
        url = self._API_URL + path
        all_args = {}
        if access_token:
            all_args["access_token"] = access_token
            all_args.update(kwargs)
        if all_args:
            url += "?" + auth.urllib_parse.urlencode(all_args)
        callback = self.async_callback(self._on_stackexchange_request, callback)
        http = self._get_auth_http_client()
        if post_args is not None:
            http.fetch(url, method="POST",
                       body=auth.urllib_parse.urlencode(post_args),
                       callback=callback)
        else:
            http.fetch(url, callback=callback)

    def _on_stackexchange_request(self, future, response):
        """Invoked as a response to the StackExchange API request. Will decode
        the response and set the result for the future to return the callback or
        raise an exception

        """
        content = escape.json_decode(response.body)
        if 'error' in content:
            future.set_exception(Exception('StackExchange error: %s' %
                                           str(content['error'])))
            return
        future.set_result(content)
