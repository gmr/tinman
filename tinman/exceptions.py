"""
Tinman Exceptions

"""

class ConfigurationException(Exception):
    def __repr__(self):
        return 'Configuration for %s is missing or invalid' % self.args[0]


class NoRoutesException(Exception):
    def __repr__(self):
        return 'No routes could be configured'