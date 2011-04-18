from mock import Mock

import sys
sys.path.insert(0, '..')

import tinman.whitelist as whitelist

# Monkey patch in our HTTPError to be an AssertionError
whitelist.HTTPError = AssertionError


# Mock up the values
class RequestMock(object):

    def __init__(self, remote_ip):

        # Mock the application object
        self.application = Mock()
        self.application.settings = dict()

        # Mock up the request object
        self.request = Mock()
        self.request.remote_ip = remote_ip

    @whitelist.whitelisted
    def whitelisted_method(self):
        return True

    @whitelist.whitelisted("11.12.13.0/24")
    def whitelisted_specific(self):
        return True


def test_empty_whitelist():

    # Mock a request
    mock = RequestMock('1.2.3.4')

    # This test should raise a ValueError exception in the whitelist
    try:
        rval = mock.whitelisted_method()
    except ValueError:
        rval = False

    # If we didn't get a value error, fail
    if rval:
        assert False, "ValueError not raised for empty whitelist"


def test_whitelisted_ip():

    # Mock a request
    mock = RequestMock('1.2.3.4')
    mock.application.settings['whitelist'] = ['1.2.3.0/24']

    try:
        rval = mock.whitelisted_method()
    except whitelist.HTTPError:
        rval = False

    # mock.whitelisted_method should return true for our mock data
    if not rval:
        assert False, "Whitelisted IP address didn't pass"


def test_non_whitelisted_ip():

    # Mock a request
    mock = RequestMock('2.2.3.4')
    mock.application.settings['whitelist'] = ['1.2.3.0/24']

    # This test should raise a ValueError exception in the whitelist
    try:
        rval = mock.whitelisted_method()
    except whitelist.HTTPError:
        rval = False

    # If we didn't get a value error, fail
    if rval:
        assert False, "whitelist did not raise HTTPError"


def test_specified_whitelisted_ip():

    # Mock a request
    mock = RequestMock('11.12.13.14')
    mock.application.settings['whitelist'] = ['1.2.3.0/24']

    try:
        rval = mock.whitelisted_specific()
    except whitelist.HTTPError:
        rval = False

    # mock.whitelisted_method should return true for our mock data
    if not rval:
        assert False, "Whitelisted IP address didn't pass"


def test_specified_non_whitelisted_ip():

    # Mock a request
    mock = RequestMock('2.2.3.4')

    # This test should raise a ValueError exception in the whitelist
    try:
        rval = mock.whitelisted_specific()
    except whitelist.HTTPError:
        rval = False

    # If we didn't get a value error, fail
    if rval:
        assert False, "whitelist did not raise HTTPError"
