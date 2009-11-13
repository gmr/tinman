#!/usr/bin/env python
"""
Project UI Modules

"""

__author__  = "Gavin M. Roy"
__email__   = "gavinmroy@gmail.com"
__date__    = "2009-11-10"
__version__ = 0.1

import tornado.web

class Generic(tornado.web.UIModule):

    def render(self):
        return self.render_string("templates/modules/generic.html")