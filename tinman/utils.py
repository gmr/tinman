# -*- coding: utf-8 -*-
"""
Functions used mainly in startup and shutdown of tornado applications
"""
import logging
import os
import os.path
import signal
import sys
import yaml

# Windows doesn't support these
try:
    import grp
except ImportError:
    grp = None
try:
    import pwd
except ImportError:
    pwd = None

from functools import wraps
from socket import gethostname

# Callback handlers
rehash_handler = None
shutdown_handler = None

# Application state for shutdown
running = False

# Get a _LOGGER for the module
_LOGGER = logging.getLogger(__name__)


def application_name():
    """
    Returns the currently running application name
    """
    return os.path.split(sys.argv[0])[1]


def hostname():
    """
    Returns the hostname for the machine we're running on
    """
    return gethostname().split(".")[0]


def daemonize(pidfile=None, user=None, group=None):
    """
    Fork the Python app into the background and close the appropriate
    "files" to detach from console. Based off of code by Jürgen Hermann and
    http://code.activestate.com/recipes/66012/

    Parameters:

    * pidfile: Pass in a file to write the pid, defaults to
               /tmp/current_process_name-pid_number.pid
    * user: User to run as, defaults to current user
    * group: Group to run as, defaults to current group
    """
    # Flush stdout and stderr
    sys.stdout.flush()
    sys.stderr.flush()

    # Set our default uid, gid
    uid, gid = -1, -1

    # Get the user id if we have a user set
    if pwd and user:
        uid = pwd.getpwnam(user).pw_uid

    # Get the group id if we have a group set
    if grp and group:
        gid = grp.getgrnam(group).gr_gid

    # Fork off from the process that called us
    pid = os.fork()
    if pid > 0:
        sys.exit(0)

    # Second fork to put into daemon mode
    pid = os.fork()
    if pid > 0:
        # exit from second parent, print eventual PID before
        sys.stdout.write('%s: started - PID # %d\n' % (application_name(),
                                                       pid))

        # Setup a pidfile if we weren't passed one
        pidfile = pidfile or \
                  os.path.normpath('/tmp/%s-%i.pid' % (application_name(),
                                                       pid))

        # Write a pidfile out
        with open(pidfile, 'w') as f:
            f.write('%i\n' % pid)

            # If we have uid or gid change the uid/gid for the file
            if uid > -1 or gid > -1:
                os.fchown(f.fileno(), uid, gid)

        # Exit the parent process
        sys.exit(0)

    # Detach from parent environment
    os.chdir(os.path.normpath('/'))
    os.umask(0)
    os.setsid()

    # Redirect stdout, stderr, stdin
    si = file('/dev/null', 'r')
    so = file('/dev/null', 'a+')
    se = file('/dev/null', 'a+', 0)
    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())

    # Set the running user
    if user and group:
        _LOGGER.info("Changing the running user:group to %s:%s", user, group)
    elif user:
        _LOGGER.info("Changing the running user to %s", user)
    elif group:
        _LOGGER.info("Changing the group to %s", group)

    # If we have a uid and it's not for the running user
    if uid > -1 and uid != os.geteuid():
            try:
                os.seteuid(uid)
                _LOGGER.debug("User changed to %s(%i)", user, uid)
            except OSError as e:
                _LOGGER.error("Could not set the user: %s", str(e))

    # if we have a gid and it's not for the current group
    if gid > -1 and gid != os.getegid():
        try:
            os.setgid(gid)
            _LOGGER.debug("Process group changed to %s(%i)", group, gid)
        except OSError as e:
            _LOGGER.error("Could not set the group: %s", str(e))

    return True


def shutdown():
    """
    Cleanly shutdown the application
    """
    global running

    # Tell all our children to stop
    if shutdown_handler:
        shutdown_handler()

    # Set the running state
    running = False


def setup_signals():
    """
    Setup the signals we want to be notified on
    """
    signal.signal(signal.SIGTERM, _shutdown_signal_handler)
    try:
        signal.signal(signal.SIGHUP, _rehash_signal_handler)
    except AttributeError:
        pass

def _shutdown_signal_handler(signum, frame):
    """
    Called on SIGTERM to shutdown the application
    """
    _LOGGER.info("SIGTERM received, shutting down")
    shutdown()


def _rehash_signal_handler(signum, frame):
    """
    Would be cool to handle this and effect changes in the config
    """
    _LOGGER.info("SIGHUP received, rehashing config")
    if rehash_handler:
        rehash_handler()


def import_namespaced_class(path):
    """
    Pass in a string in the format of foo.Bar, foo.bar.Baz, foo.bar.baz.Qux
    and it will return a handle to the class
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


def load_yaml_file(config_file):
    """ Load the YAML configuration file from disk or error out
    if not found or parsable.

    :param str config_file: Full path to the filename
    :returns: dict

    """
    try:
        with file(config_file, 'r') as handle:
            config = yaml.load(handle)

    except IOError:
        sys.stderr.write('Configuration file not found "%s"\n' % config_file)
        sys.exit(1)

    except yaml.scanner.ScannerError as err:
        sys.stderr.write('Invalid configuration file "%s":\n%s\n' %\
                         (config_file, err))
        sys.exit(1)

    return config
