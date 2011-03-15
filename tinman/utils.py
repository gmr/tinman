# -*- coding: utf-8 -*-
"""
Functions used mainly in startup and shutdown of tornado applications
"""
import grp
import logging
import os
import os.path
import pwd
import signal
import sys
import yaml

from functools import wraps
from socket import gethostname
from tornado.options import enable_pretty_logging

# Callback handlers
rehash_handler = None
shutdown_handler = None

# Application state for shutdown
running = False


def log_method_call(method):
    """
    Logging decorator to send the method and arguments to logging.debug
    """
    @wraps(method)
    def debug_log(*args, **kwargs):

        if logging.getLogger('').getEffectiveLevel() == logging.DEBUG:

            # Get the class name of what was passed to us
            try:
                class_name = args[0].__class__.__name__
            except AttributeError:
                class_name = 'Unknown'
            except IndexError:
                class_name = 'Unknown'

            # Build a list of arguments to send to the logging
            log_args = list()
            for x in xrange(1, len(args)):
                log_args.append(args[x])
            if len(kwargs) > 1:
                log_args.append(kwargs)

            # If we have arguments, log them as well, otherwise just the method
            if log_args:
                logging.debug("%s.%s(%r) Called", class_name, method.__name__,
                             log_args)
            else:
                logging.debug("%s.%s() Called", class_name, method.__name__)

        # Actually execute the method
        return method(*args, **kwargs)

    # Return the debug_log function to the python stack for execution
    return debug_log


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
    if user:
        uid = pwd.getpwnam(user).pw_uid

    # Get the group id if we have a group set
    if group:
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
        logging.info("Changing the running user:group to %s:%s", user, group)
    elif user:
        logging.info("Changing the running user to %s", user)
    elif group:
        logging.info("Changing the group to %s", group)

    # If we have a uid and it's not for the running user
    if uid > -1 and uid != os.geteuid():
            try:
                os.seteuid(uid)
                logging.debug("User changed to %s(%i)", user, uid)
            except OSError as e:
                logging.error("Could not set the user: %s", str(e))

    # if we have a gid and it's not for the current group
    if gid > -1 and gid != os.getegid():
        try:
            os.setgid(gid)
            logging.debug("Process group changed to %s(%i)", group, gid)
        except OSError as e:
            logging.error("Could not set the group: %s", str(e))

    return True


def load_configuration_file(config_file):
    """
    Load our YAML configuration file from disk or error out
    if not found or parsable
    """
    try:
        with file(config_file, 'r') as f:
            config = yaml.load(f)

    except IOError:
        sys.stderr.write('Configuration file not found "%s"\n' % config_file)
        sys.exit(1)

    except yaml.scanner.ScannerError as err:
        sys.stderr.write('Invalid configuration file "%s":\n%s\n' % \
                         (config_file, err))
        sys.exit(1)

    return config


def setup_logging(config, debug=False):
    """
    Setup the logging module to respect our configuration values.
    Expects a dictionary called config with the following parameters

    * directory:   Optional log file output directory
    * filename:    Optional filename, not needed for syslog
    * format:      Format for non-debug mode
    * level:       One of debug, error, warning, info
    * handler:     Optional handler
    * syslog:      If handler == syslog, parameters for syslog
      * address:   Syslog address
      * facility:  Syslog facility

    Passing in debug=True will disable any log output to anything but stdout
    and will set the log level to debug regardless of the config.
    """
    # Set logging levels dictionary
    logging_levels = {'debug':    logging.DEBUG,
                      'info':     logging.INFO,
                      'warning':  logging.WARNING,
                      'error':    logging.ERROR,
                      'critical': logging.CRITICAL}

    # Get the logging value from the dictionary
    logging_level = config['level']

    if debug:

        # Override the logging level to use debug mode
        config['level'] = logging.DEBUG

        # If we have specified a file, remove it so logging info goes to stdout
        if 'filename' in config:
            del config['filename']

    else:

        # Use the configuration option for logging
        config['level'] = logging_levels.get(config['level'], logging.NOTSET)

    # Pass in our logging config
    logging.basicConfig(**config)
    logging.info('Log level set to %s' % logging_level)

    # Get the default logger
    default_logging = logging.getLogger()

    # Remove the default stream handler
    stream_handler = None
    for handler in default_logging.handlers:
        if isinstance(handler, logging.StreamHandler):
            stream_handler = handler
            break

    # Use colorized output
    if config['level'] == logging.DEBUG:
        enable_pretty_logging()

    # If we have supported handler
    elif 'handler' in config:

        # If we want to syslog
        if config['handler'] == 'syslog':

            facility = config['syslog']['facility']
            import logging.handlers as handlers

            # If we didn't type in the facility name
            if facility in handlers.SysLogHandler.facility_names:

                # Create the syslog handler
                address = config['syslog']['address']
                facility = handlers.SysLogHandler.facility_names[facility]
                syslog = handlers.SysLogHandler(address=address,
                                                facility=facility)
                # Add the handler
                default_logging.addHandler(syslog)

                # Remove the StreamHandler
                if stream_handler:
                    default_logging.removeHandler(stream_handler)
            else:
                logging.error('%s:Invalid facility, syslog logging aborted',
                              application_name())


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
    signal.signal(signal.SIGHUP, _rehash_signal_handler)


def _shutdown_signal_handler(signum, frame):
    """
    Called on SIGTERM to shutdown the application
    """
    logging.info("SIGTERM received, shutting down")
    shutdown()


def _rehash_signal_handler(signum, frame):
    """
    Would be cool to handle this and effect changes in the config
    """
    logging.info("SIGHUP received, rehashing config")
    if rehash_handler:
        rehash_handler()
