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
DataLayer is just an empty stub singleton class for your data. 
"""
 
class DataLayer:

    # Handle for shared state
    __shared_state = {}        
    
    def __init__(self):

        # Set the dict to the shared state dict    
        self.__dict__ = self.__shared_state
        
#        Mongo Connection
#        self.connection = Connection()
#        self.database = self.connection.project
        pass
