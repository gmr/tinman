Tinman
======
A collection of useful decorators and modules for Tornado.

Features
--------
Decorators:

- tinman.whitelisted: Vaidates the requesting IP address against a list of ip
  address blocks specified in Application.settings

  Example:

      # Define the whitelist as part of your application settings
      settings['whitelist'] = ['10.0.0.0/8',
                               '192.168.1.0/24',
                               '1.2.3.4/32']

      application = Application(routes, **settings)

      # Specify the decorator in each method of your RequestHandler class
      # where you'd like to enforce the whitelist
      class MyClass(tornado.web.RequestHandler):

          @tinman.whitelisted
          def get(self):
              self.write("IP was whitelisted")
