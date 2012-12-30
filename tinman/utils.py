"""
@TODO see if we can move these functions to a more appropriate spot

"""
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

    :rtype: class

    """
    # Split up our string containing the import and class
    parts = path.split('.')

    # Build our strings for the import name and the class name
    import_name = '.'.join(parts[0:-1])
    class_name = parts[-1]

    # get the handle to the class for the given import
    class_handle = getattr(__import__(import_name, fromlist=class_name),
                           class_name)

    # Return the class handle
    return class_handle
