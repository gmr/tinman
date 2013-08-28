"""
@TODO see if we can move these functions to a more appropriate spot

"""
import importlib
import os
import sys
from socket import gethostname


def application_name():
    """Returns the currently running application name

    :rtype: str

    """
    return os.path.split(sys.argv[0])[1]


def hostname():
    """Returns the hostname for the machine we're running on

    :rtype: str

    """
    return gethostname().split(".")[0]


def import_namespaced_class(path):
    """Pass in a string in the format of foo.Bar, foo.bar.Baz, foo.bar.baz.Qux
    and it will return a handle to the class

    :param str path: The object path
    :rtype: class

    """
    parts = path.split('.')
    return getattr(importlib.import_module('.'.join(parts[0:-1])), parts[-1])
