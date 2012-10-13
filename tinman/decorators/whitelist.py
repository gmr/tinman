"""
Tinman Whitelist Module

"""
import ipaddr
from tornado import web
import types


def whitelisted(argument=None):
    """Decorates a method requiring that the requesting IP address is
    whitelisted. Requires a whitelist value as a list in the
    Application.settings dictionary. IP addresses can be an individual IP
    address or a subnet.

    Examples:
        ['10.0.0.0/8','192.168.1.0/24', '1.2.3.4/32']

    :param list argument: List of whitelisted ip addresses or blocks
    :raises: web.HTTPError
    :raises: ValueError
    :rtype: any

    """
    def is_whitelisted(remote_ip, whitelist):
        """Check to see if an IP address is whitelisted.

        :param str ip_address: The IP address to check
        :param list whitelist: The whitelist to check against
        :rtype: bool

        """
        # Convert the ip into a long int version of the ip address
        user_ip = ipaddr.IPv4Address(remote_ip)

        # Loop through the ranges in the whitelist and check
        if any([user_ip in ipaddr.IPv4Network(entry) for entry in whitelist]):
            return True

        return False

    # If the argument is a function then there were no parameters
    if type(argument) is types.FunctionType:

        def wrapper(self, *args, **kwargs):
            """Check the whitelist against our application.settings dictionary
            whitelist key.

            :rtype: any
            :raises: web.HTTPError

            """
            # Validate we have a configured whitelist
            if 'whitelist' not in self.application.settings:
                raise ValueError('whitelist not found in Application.settings')

            # If the IP address is whitelisted, call the wrapped function
            if is_whitelisted(self.request.remote_ip,
                              self.application.settings['whitelist']):

                # Call the original function, IP is whitelisted
                return argument(self, *args, **kwargs)

            # The ip address was not in the whitelist
            raise web.HTTPError(403)

        # Return the wrapper method
        return wrapper

    # They passed in string or list?
    else:

        # Convert a single ip address to a list
        if isinstance(argument, str):
            argument = [argument]

        # Make sure it's a list
        elif not isinstance(argument, list):
            raise ValueError('whitelisted requires no parameters or '
                             'a string or list')

        def argument_wrapper(method):
            """Wrapper for a method passing in the IP addresses that constitute
            the whitelist.

            :param method method: The method being wrapped
            :rtype: any
            :raises: web.HTTPError

            """
            def validate(self, *args, **kwargs):
                """
                Validate the ip address agross the list of ip addresses
                passed in as a list
                """
                if is_whitelisted(self.request.remote_ip, argument):

                    # Call the original function, IP is whitelisted
                    return method(self, *args, **kwargs)

                # The ip address was not in the whitelist
                raise web.HTTPError(403)

            # Return the validate method
            return validate

        # Return the wrapper method
        return argument_wrapper
