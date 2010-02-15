#!/usr/bin/env python
"""
Tinman Data Layer
"""

__author__  = "Gavin M. Roy"
__email__   = "gavinmroy@gmail.com"
__date__    = "2010-02-07"
__version__ = 0.1

from new import classobj
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
                session = sqlalchemy.orm.sessionmaker(bind=driver['engine'])
                driver['session'] = session()
                driver['metadata'] = sqlalchemy.MetaData(bind=driver['engine'])

        else:
            logging.error('Unknown data driver type')

    def commit(self):
        global driver
        driver['session'].commit()        

    def create_all(self):
        global driver
        driver['metadata'].create_all()
    
    def flush(self):
        global driver
        driver['session'].flush()

    def delete(self, obj):
        global driver
        driver['session'].delete(obj)

class Model(object):

    # SQL Alchemy Model to be extended
    from sqlalchemy import exceptions, Table, Column, MetaData, ForeignKey, \
                            Boolean, Date, DateTime, Float, Integer, String, \
                            Interval, LargeBinary, Numeric, SmallInteger, \
                            Text, Unicode, UnicodeText

    count = 0
    schema_name = None

    def __init__(self, *args, **kwargs):
        from sqlalchemy.orm import mapper

        # Get the driver
        global driver
        
        # Define our table name from our class name
        table_name = self.__class__.__name__.lower()

        # Look to see if the class already has our instance
        if driver['models'].has_key(table_name):

            # Assign our table instance stored in the global driver stack
            self.table = driver['models'][table_name]
            return

        if not self.schema_name:
            self.schema_name = 'public'

        # Create our table object
        self.table = self.Table(table_name, driver['metadata'], schema=self.schema_name)

        # A dict of our columns
        self.columns = {}

        # Iterate through the attributes to add schema to the table
        for attr in self.__class__.__dict__:
            if type(self.__class__.__dict__[attr]).__name__ == 'Column':
                self.table.append_column(self.__class__.__dict__[attr])
                self.columns[attr] = None

        # Dynamically create or data object
        DataObject = type('DataObject',(object,),self.columns)

        # Map the dynamic object
        mapper(DataObject, self.table)

        # Create our internal object to use for data manipulation
        self.obj = DataObject()

        # Query based upon a kwargs        
        if len(kwargs):
        
            # A query object for our model object
            query = driver['session'].query(DataObject)
            self.results = query.filter_by(**kwargs).all()
            self.count = len(self.results)

            # If it's only one row, map it to the our model object
            if len(self.results) == 1:
                for column in self.columns:
                    self.__dict__[column] = self.results[0].__dict__[column]
            
        # Pop this handle in the global driver stack
        driver['models'][table_name] = self.table

    def create(self):
        self.table.create()

    def save(self):
        global driver

        for column in self.columns:
            if self.__dict__.has_key(column):
                self.obj.__dict__[column] = self.__dict__[column]

        driver['session'].add(self.obj)
        driver['session'].commit()
