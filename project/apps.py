#!/usr/bin/env python
"""
Project Core Application Classes

"""

__author__  = "Gavin M. Roy"
__email__   = "gavinmroy@gmail.com"
__date__    = "2009-11-10"
__version__ = 0.1

import project.data
import project.handler
        
class Home(project.handler.RequestHandler):

    def get(self):
        self.render('templates/apps/home.html', title='Hello, World!');