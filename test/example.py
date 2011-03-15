from tinman.utils import log_method_call
from tornado.web import RequestHandler

class Home(RequestHandler):

    @log_method_call
    def get(self):
        self.write("Hello, World!")

class Catchall(RequestHandler):

    @log_method_call
    def get(self, parameters):
        self.write("URI: %s" % parameters)
