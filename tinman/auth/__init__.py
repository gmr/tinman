from basic import require_basic_auth
from digest import digest_auth
from ldapauth import auth_user_ldap

class AmITesting(object):
    def __init__(self):
        self.am_i = False

AM_I_TESTING = AmITesting()
