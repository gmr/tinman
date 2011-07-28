"""
A tornado.web.RequestHandler decorator that provides HTTP Basic Authentication. 

The decorator takes two arguments: 

    1. realm: the realm that's typically presented to the user during a
    challenge request for authentication.

    2. validate_callback: A callable that's used to validate the credentials.
    The callable will receive the username and password provided by the end
    user in a challenge.

Example usage (also see helloworld_basic.py in the examples): 

    # define the validation callback.
    def validate(uname, passwd):
        creds = {'auth_username': 'jonesy', 'auth_password': 'foobar'}
        if uname == creds['auth_username'] and passwd == creds['auth_password']:
            return True
        else:
            return False

    # now define the RequestHandler, using the decorator.
    @require_basic_auth('AuthRealm', validate)
    class MainHandler(tornado.web.RequestHandler):
        def get(self):
            self.write("Hello, world - Tornado %s" % tornado.version)

""" 

import base64

def require_basic_auth(realm, validate_callback):
    def require_basic_auth_decorator(handler_class):
        def wrap_execute(handler_execute):
            def require_basic_auth(handler, kwargs):
                def create_auth_header():
                    print("Creating auth header")
                    handler.set_status(401)
                    handler.set_header('WWW-Authenticate', 'Basic realm=%s' % realm)
                    handler._transforms = []
                    handler.finish()

                auth_header = handler.request.headers.get('Authorization')
                if auth_header is None or not auth_header.startswith('Basic '):
                    create_auth_header()
                else:
                    auth_decoded = base64.decodestring(auth_header[6:])
                    basicauth_user, basicauth_pass = auth_decoded.split(':', 2)
                    if validate_callback(basicauth_user, basicauth_pass):
                        return True
                    else:
                        create_auth_header()
            def _execute(self, transforms, *args, **kwargs):
                if not require_basic_auth(self, kwargs):
                    return False
                return handler_execute(self, transforms, *args, **kwargs)
            return _execute

        handler_class._execute = wrap_execute(handler_class._execute)
        return handler_class
    return require_basic_auth_decorator
