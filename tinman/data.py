#!/usr/bin/env python
"""
Tinman Data Layer
"""

__author__  = "Gavin M. Roy"
__email__   = "gavinmroy@gmail.com"
__date__    = "2010-02-07"
__version__ = 0.1

import logging

# A persistent dictionary for our database connection and elements
driver = {'models': {}}

class DataLayer:

    def __init__(self, configuration):
    
        global driver
        
        # Carry the configuration in the document
        self.configuration = configuration

        # If it's an SQLAlchemy Request
        if self.configuration.has_key('SQLAlchemy'):
            import sqlalchemy
            import sqlalchemy.orm
            
            if not driver.has_key('engine'):
                logging.debug('Creating new SQLAlchemy engine instance')
                driver['engine'] = sqlalchemy.create_engine(self.configuration['SQLAlchemy']['url'])
                driver['session'] = sqlalchemy.orm.sessionmaker(bind=driver['engine'])
                driver['metadata'] = sqlalchemy.MetaData()
                driver['metadata'].bind = driver['engine']
                
        else:
            logging.error('Unknown data driver type')
    
    def create_all(self):
        global driver
        driver['metadata'].create_all()
    
            
class Model(object):
    
    # SQL Alchemy Model to be extended
    from sqlalchemy import schema, Table, Column, Integer, String, MetaData, ForeignKey

    def __init__(self):
        
        # Get the driver
        global driver
    
        table_name = self.__class__.__name__.lower()
    
        # Look to see if the class already has our instance
        if driver['models'].has_key(table_name):
        
            # Assign our table instance stored in the global driver stack
            self.table = driver['models'][table_name]
            return
                
        # Create our table object
        self.table = self.Table(table_name, driver['metadata'])
        
        # Iterate through the attributes to add schema to the table
        for attr in self.__class__.__dict__:
            if type(self.__class__.__dict__[attr]).__name__ == 'Column':
                self.table.append_column(self.__class__.__dict__[attr])

        # Pop this handle in the global driver stack    
        driver['models'][table_name] = self.table