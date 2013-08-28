"""
Tinman provides a base RequestHandler extending Tornado's web.RequestHandler
adding additional behaviors across all RequestHandlers that use it.

"""
import json
from tornado import web


class RequestHandler(web.RequestHandler):
    """A base RequestHandler that adds the following functionality:

    - If sending a dict, checks the user-agent string for curl and sends an
      indented, sorted human-readable JSON snippet.
    - Toggles the ensure_ascii flag in json.dumps
    - Overrides the default behavior for unimplemented methods to instead set
    the status and look to the allow object attribute for methods that can be
    allowed. This is useful for when using NewRelic since the newrelic agent
    will catch the normal exceptions thrown as errors and trigger false alerts.

    To use, do something like::

        from tinman import handlers

        class Handler(handlers.RequestHandler):

            allow = [handlers.GET, handlers.POST]

            def get(self, *args, **kwargs):
                self.write({'foo': 'bar'})

            def post(self, *args, **kwargs):
                self.write({'message': 'Saved'})

    """
    allow = []

    def _method_not_allowed(self):
        self.set_header('Allow', ', '.join(self.allow))
        self.set_status(405, 'Method Not Allowed')

    def head(self, *args, **kwargs):
        """Implement the HTTP HEAD method

        :param list args: Positional arguments
        :param dict kwargs: Keyword arguments

        """
        self._method_not_allowed()

    def get(self, *args, **kwargs):
        """Implement the HTTP GET method

        :param list args: Positional arguments
        :param dict kwargs: Keyword arguments

        """
        self._method_not_allowed()

    def post(self, *args, **kwargs):
        """Implement the HTTP POST method

        :param list args: Positional arguments
        :param dict kwargs: Keyword arguments

        """
        self._method_not_allowed()

    def delete(self, *args, **kwargs):
        """Implement the HTTP DELETE method

        :param list args: Positional arguments
        :param dict kwargs: Keyword arguments

        """
        self._method_not_allowed()

    def patch(self, *args, **kwargs):
        """Implement the HTTP PATCH method

        :param list args: Positional arguments
        :param dict kwargs: Keyword arguments

        """
        self._method_not_allowed()

    def put(self, *args, **kwargs):
        """Implement the HTTP PUT method

        :param list args: Positional arguments
        :param dict kwargs: Keyword arguments

        """
        self._method_not_allowed()

    def options(self, *args, **kwargs):
        """Implement the HTTP OPTIONS method

        :param list args: Positional arguments
        :param dict kwargs: Keyword arguments

        """
        self._method_not_allowed()

    def write(self, chunk):
        """Writes the given chunk to the output buffer.

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
