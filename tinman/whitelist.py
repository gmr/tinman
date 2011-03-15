"""
Tinman Whitelist Module
"""
__author__ = "Gavin M. Roy"
__email__ = "gmr@myyearbook.com"
__date__ = "2011-03-13"
__version__ = 0.1

from functools import wraps
from ipaddr import IPv4Network, IPv4Address
from tornado.web import HTTPError
from types import FunctionType

def whitelisted(argument=None):
    """
    Decorates a method requiring that the requesting IP address is whitelisted

    Requires a whitelist value as a list in the Application.settings dictionary
    Ip addresses can be an individual IP address or a subnet.

    Examples:
        ['10.0.0.0/8','192.168.1.0/24', '1.2.3.4/32']
    """
    def is_whitelisted(remote_ip, whitelist):

        # Convert the ip into a long int version of the ip address
        user_ip = IPv4Address(remote_ip)

        # Loop through the ranges in the whitelist and check
        if any([user_ip in IPv4Network(entry) for entry in whitelist]):
            return True

        return False

    # If the argument is a function then there were no parameters
    if type(argument) is FunctionType:

        def wrapper(self, *args, **kwargs):
            """
            Check the whitelist against our application.settings dictionary
            whitelist key
            """
            # Validate we have a configured whitelist
            if 'whitelist' not in self.application.settings:
                raise ValueError("whitelist not found in Application.settings")

            if is_whitelisted(self.request.remote_ip,
                              self.application.settings['whitelist']):

                # Call the original function, IP is whitelisted
                return argument(self, *args, **kwargs)

            # The ip address was not in the whitelist
            raise HTTPError(403)

        return wrapper

    # They passed in string or list?
    else:
        # Convert a single ip address to a list
        if isinstance(argument, str):
            argument = [argument]

        # Make sure it's a list
        elif not isinstance(argument, list):
            err = "whitelisted requires no parameters or a string or list"
            raise ValueError(err)

        def argument_wrapper(method):

            def validate(self, *args, **kwargs):
                """
                Validate the ip address agross the list of ip addresses
                passed in as a list
                """
                if is_whitelisted(self.request.remote_ip, argument):

                    # Call the original function, IP is whitelisted
                    return method(self, *args, **kwargs)

                # The ip address was not in the whitelist
                raise HTTPError(403)

            return validate

        return argument_wrapper
