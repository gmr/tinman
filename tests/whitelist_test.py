import mock
import sys
from tornado import web
try:
    import unittest2 as unittest
except ImportError:
    import unittest
sys.path.insert(0, '..')


from tinman import whitelist


# Mock up the values
class RequestMock(object):

    def __init__(self, remote_ip):

        # Mock the application object
        self.application = mock.Mock()
        self.application.settings = dict()

        # Mock up the request object
        self.request = mock.Mock()
        self.request.remote_ip = remote_ip

    @whitelist.whitelisted
    def whitelisted_method(self):
        return True

    @whitelist.whitelisted("11.12.13.0/24")
    def whitelisted_specific(self):
        return True


class WhitelistTests(unittest.TestCase):

    def setUp(self):
        self.request = self._get_request()

    def tearDown(self):
        del self.request

    def _get_request(self, ip_address='1.2.3.4'):
        request = RequestMock(ip_address)
        request.application.settings['whitelist'] = ['1.2.3.0/24']
        return request

    def test_empty_whitelist(self):
        request = RequestMock('1.2.3.4')
        self.assertRaises(ValueError,
                          request.whitelisted_method,
                          'ValueError not raised for empty whitelist')

    def test_whitelisted_ip(self):
        self.assertTrue(self.request.whitelisted_method(),
                        'Whitelisted IP address did not pass')

    def test_non_whitelisted_ip(self):
        request = self._get_request('2.2.3.4')
        self.assertRaises(web.HTTPError,
                          request.whitelisted_method,
                          'whitelist did not raise whitelist.HTTPError')

    def test_specific_whitelisted_ip(self):
        request = self._get_request('11.12.13.14')
        self.assertTrue(request.whitelisted_specific(),
                        'Whitelisted IP address did not pass')

    def test_specific_non_whitelisted_ip(self):
        self.assertRaises(web.HTTPError,
                          self.request.whitelisted_specific,
                          'whitelist did not raise whitelist.HTTPError')


    def test_invalid_whitelisted_ip(self):
        try:
            @whitelist.whitelisted(1234)
            def whitelisted_invalid(self):
                return True
        except ValueError:
            return
        assert False, 'invalid specified whitelist did not raise ValueError'
