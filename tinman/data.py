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
driver = {}

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
                print driver
        
        else:
            logging.error('Unknown data driver type')