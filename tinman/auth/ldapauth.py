"""
See an example that uses basic auth with an LDAP 
backend in examples/helloworld_basic_ldap.py

"""
import ldap
import logging

# where to start the search for users
LDAP_SEARCH_BASE = 'ou=People,dc=yourdomain,dc=com'

# the server to auth against
LDAP_URL = 'ldap://ldap.yourdomain.com'

# The attribute we try to match the username against.
LDAP_UNAME_ATTR = 'uid'

# The attribute we need to retrieve in order to perform a bind.
LDAP_BIND_ATTR = 'dn'

# Whether to use LDAPv3. Highly recommended.
LDAP_VERSION_3 = True

def auth_user_ldap(uname, pwd):
    """
    Attempts to bind using the uname/pwd combo passed in.
    If that works, returns true. Otherwise returns false.

    """
    if not uname or not pwd:
        logging.error("Username or password not supplied")
        return False

    ld = ldap.initialize(LDAP_URL)
    if LDAP_VERSION_3:
        ld.set_option(ldap.VERSION3, 1)
    ld.start_tls_s()
    udn = ld.search_s(LDAP_SEARCH_BASE, ldap.SCOPE_ONELEVEL,
                           '(%s=%s)' % (LDAP_UNAME_ATTR,uname), [LDAP_BIND_ATTR])
    if udn:
        try:
            bindres = ld.simple_bind_s(udn[0][0], pwd)
        except ldap.INVALID_CREDENTIALS, ldap.UNWILLING_TO_PERFORM:
            logging.error("Invalid or incomplete credentials for %s", uname)
            return False
        except Exception as out:
            logging.error("Auth attempt for %s had an unexpected error: %s",
                         uname, out)
            return False
        else:
            return True
    else:
        logging.error("No user by that name")
        return False


