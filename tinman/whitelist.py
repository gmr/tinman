"""
Tinman Whitelist Module
"""
__author__ = "Gavin M. Roy"
__email__ = "gmr@myyearbook.com"
__date__ = "2011-03-13"
__version__ = 0.1

from functools import wraps
from ipaddr import IPv4
from tornado.web import HTTPError


def whitelisted(method):
    """
    Decorates a method requiring that the requesting IP address is whitelisted

    Requires a whitelist value as a list in the Application.settings dictionary
    Ip addresses can be an individual IP address or a subnet.

    Examples:
        ['10.0.0.0/8','192.168.1.0/24', '1.2.3.4/32']
    """
    @wraps(method)
    def wrapper(self, *args, **kwargs):

        # Validate we have a configured whitelist
        if 'whitelist' not in self.application.settings:
            raise ValueError("whitelist is not found in Application.settings")

        # Convert the ip into a long int version of the ip address
        user_ip = IPv4(self.request.remote_ip).ip

        # By default the IP Address is whitelisted
        whitelisted = False

        # Loop through the ranges in the whitelist and check
        for whitelist_ip in self.application.settings['whitelist']:

            # Use IPv4 to return an ip address we can range check against
            wl_ip = IPv4(whitelist_ip)

            # if ip == the network's base IP (which is the case if we're giving
            # it a straight IP with no range suffix) OR if ip is within the
            # subnet for the given range (a machine's address in a subnet can't
            # ever be the broadcast address so it's < not <=)
            if user_ip == wl_ip.network or \
               (user_ip >= wl_ip.network and \
                user_ip < wl_ip.broadcast):

                # Call the original function, IP is whitelisted
                return method(self, *args, **kwargs)

        # The ip address was not in the whitelist
        raise HTTPError(403)

    # Return the result of the require function
    return wrapper
