"""
External non-disk template loaders

"""
__author__ = 'Gavin M. Roy'
__email__ = 'gmr@myyearbook.com'
__since__ = '2011-08-25'

import json
import logging
from tornado import escape
from tornado import httpclient
from tornado import template


class CouchDBLoader(template.BaseLoader):
    """
    Extends the tornado.template.Loader allowing for templates to be loaded out
    of CouchDB.

    Templates in CouchDB should have have an _id matching the value of the name
    that is passed into load. _id's may have /'s in them. The template itself
    should be in the template node of the JSON document in CouchDB.

    """
    def __init__(self, base_url, **kwargs):
        """Creates a template loader.

        """
        template.BaseLoader.__init__(self, '/', **kwargs)
        #super(CouchDBLoader, self).__init__(**kwargs)
        self._logger = logging.getLogger('tinman.loader')
        self._base_url = base_url.rstrip('/')
        self._logger.info('CouchDBLoader initialized with base URL of %s',
                          self._base_url)
        self._http_client = httpclient.HTTPClient()

    def load(self, name, parent_path=None):
        """Loads a template.
        """
        if name not in self.templates:
            self.templates[name] = self._create_template(name)

        return self.templates[name]

    def _create_template(self, name):

        # Construct the URL
        url = '%s/%s' % (self._base_url, escape.url_escape(name))

        # Fetch the data from couchdb
        self._logger.debug('Making HTTP GET request to %s', url)
        response = self._http_client.fetch(url)

        # Load the data from the JSON string
        data = json.loads(response.body)

        # Return the template
        return template.Template(data['template'], name=name, loader=self)
