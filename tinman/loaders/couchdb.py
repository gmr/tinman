"""
The CouchDB template loader allows for Tornado templates to be stored in CouchDB
and retrieved on demand and supports all of the syntax of including and
extending templates that you'd expect in any other template loader.

"""
import json
import logging
from tornado import escape
from tornado import httpclient
from tornado import template

LOGGER = logging.getLogger(__name__)


class CouchDBLoader(template.BaseLoader):
    """Extends the tornado.template.Loader allowing for templates to be loaded
    out of CouchDB.

    Templates in CouchDB should have have an _id matching the value of the name
    that is passed into load. _id's may have /'s in them. The template itself
    should be in the template node of the JSON document in CouchDB.

    """
    def __init__(self, base_url, **kwargs):
        """Creates a template loader.

        :param str base_url: The base URL for the CouchDB server

        """
        super(CouchDBLoader, self).__init__('/', **kwargs)
        self._base_url = base_url.rstrip('/')
        LOGGER.info('Initialized with base URL of %s', self._base_url)
        self._http_client = httpclient.HTTPClient()

    def load(self, name, parent_path=None):
        """Loads a template.

        :param str name: The template name
        :param str parent_path: The optional path for a parent document
        :rtype: tornado.template.Template

        """
        if name not in self.templates:
            self.templates[name] = self._create_template(name)
        return self.templates[name]

    def _create_template(self, name):
        """Create an instance of a tornado.template.Template object for the
        given template name.

        :param str name: The name/path to the template
        :rtype: tornado.template.Template

        """
        url = '%s/%s' % (self._base_url, escape.url_escape(name))
        LOGGER.debug('Making HTTP GET request to %s', url)
        response = self._http_client.fetch(url)
        data = json.loads(response.body, ensure_ascii=False)
        return template.Template(data['template'], name=name, loader=self)
