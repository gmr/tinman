#!/usr/bin/env python
"""
Tinman Data Layer
"""

__author__  = "Gavin M. Roy"
__email__   = "gavinmroy@gmail.com"
__date__    = "2010-02-07"
__version__ = 0.2

import logging

# A persistent dictionary for our database connection and elements
connections = {}

class DataLayer:

    def __init__(self, configuration):

        global connections

        # Carry the configuration in the document
        self.configuration = configuration

        for connection in configuration:
            if connection.has_key('driver'):
                if connection['driver'] == 'SQLAlchemy':
                    import sqlalchemy
                    import sqlalchemy.orm
                    if not connections.has_key(connection['name']):
                        connections[connection['name']] = {'driver': connection['driver']}
                        logging.debug('Creating new SQLAlchemy engine instance')
                        connections[connection['name']]['engine'] = sqlalchemy.create_engine(connection['dsn'])
                        session = sqlalchemy.orm.sessionmaker(bind=connections[connection['name']]['engine'])
                        connections[connection['name']]['session'] = session()
                        connections[connection['name']]['metadata'] = sqlalchemy.MetaData(bind=connections[connection['name']]['engine'])
                else:
                    logging.error('Unknown data driver type')
            else:
                logging.error('Connection is missing the driver setting')

        print connections

    def commit(self):
        global connections
        for connection in connection:
            if connection['driver'] == 'SQLAlchemy':
                connection['session'].commit()

    def create_all(self):
        global connections
        for connection in connection:
            if connection['driver'] == 'SQLAlchemy':
                connection['metadata'].create_all()

    def flush(self):
        global connections
        for connection in connection:
            if connection['driver'] == 'SQLAlchemy':
                connection['session'].flush()
