#!/usr/bin/env python
"""
Project Data Layer

"""

__author__  = "Gavin M. Roy"
__email__   = "gavinmroy@gmail.com"
__date__    = "2009-11-10"
__version__ = 0.1

#from pymongo.connection import Connection
 
"""
Mongo is a Singleton handler for our MongoDB usage

In this case it could be any data object, but I'm playing with MongoDB these days
 
"""
 
class Mongo:
 
    def __call__(self):
        return self
        
    def __init__(self):
        pass
#        self.connection = Connection()
#        self.database = self.connection.project