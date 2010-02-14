#!/usr/bin/env python
"""
Project Core Application Classes

"""

__author__  = "Gavin M. Roy"
__email__   = "gavinmroy@gmail.com"
__date__    = "2009-11-10"
__version__ = 0.1

import tinman.data as data
import tinman.models.user as user
import tinman.handler as handler

class Home(handler.RequestHandler):

    def get(self):
        
        gmr = user.TinmanUser()

        #self.data.create_all()      
        gmr.username = 'gmr'
        gmr.email = 'gavinmroy@gmail.com'
        gmr.password = 'foo'
        gmr.save()
          
        self.render('templates/apps/home.html');
