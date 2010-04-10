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

    session = None

    def __init__(self, configuration):

        global connections

        # Carry the configuration in the document
        self.configuration = configuration

        for connection in configuration:
            if connection.has_key('driver'):
                if connection['driver'] == 'SQLAlchemy':
                    import sqlalchemy
                    import sqlalchemy.orm
                    
                    # Use auto-commit based upon config file
                    auto_commit = False
                    if connection.has_key('session'):
                        if connection['session'].has_key('autocommit'):
                            auto_commit = connection['session']['autocommit']
                    
                    if not connections.has_key(connection['name']):
                        connections[connection['name']] = {'driver': connection['driver']}
                        logging.debug('Creating new SQLAlchemy engine instance')
                        connections[connection['name']]['engine'] = sqlalchemy.create_engine(connection['dsn'])
                        session = sqlalchemy.orm.sessionmaker(bind=connections[connection['name']]['engine'], 
                                                              autocommit=auto_commit, 
                                                              autoflush=True)
                        connections[connection['name']]['session'] = session()
                        connections[connection['name']]['metadata'] = sqlalchemy.MetaData(bind=connections[connection['name']]['engine'])

                    if not self.session:
                        logging.debug('Setting default session to "%s"' % connection['name'])
                        self.session = connections[connection['name']]['session']
                else:
                    logging.error('Unknown data driver type')
            else:
                logging.error('Connection is missing the driver setting')

    def bind_module(self, connection_name, module):
        logging.debug('Binding %s to %s' % (module, connection_name))
        module.metadata.bind = connections[connection_name]['engine']

    def begin(self, connection_name=None):
        global connections
        if connection_name:
            logging.debug('Beginning session "%s"' % connection_name)
            connections[connection_name]['session'].begin()
        else:
            for connection in connections:
                if connections[connection]['driver'] == 'SQLAlchemy':
                    logging.debug('Beginning session "%s"' % connection)
                    connections[connection]['session'].begin()

    def commit(self, all=False):
        global connections
        if not all:
            logging.debug('Committing active connection')
            self.session.commit()
        else:
            for connection in connections:
                if connections[connection]['driver'] == 'SQLAlchemy':
                    logging.debug('Committing connection "%s"' % connection)
                    connections[connection]['session'].commit()

    def create_all(self):
        global connections
        for connection in connections:
            if connections[connection]['driver'] == 'SQLAlchemy':
                logging.debug('Creating all for session "%s"' % connection)
                connections[connection]['session'].create_all()

    def dirty(self, connection_name=None):
        global connections
        if connection_name:
            if len(connections[connection_name]['session'].dirty):
                return True
        else:
            for connection in connections:
                if connections[connection]['driver'] == 'SQLAlchemy':
                    if len(connections[connection]['session'].dirty):
                        return True
        return False

    def flush(self):
        global connections
        for connection in connections:
            if connections[connection]['driver'] == 'SQLAlchemy':
                logging.debug('Flushing session "%s"' % connection)
                connections[connection]['session'].flush()

    def select(self, connection_name, query):
        global connections
        return connections[connection_name]['engine'].execute(query)
    
    def set_session(self, connection_name):
        global connections
        logging.debug('Setting active data session to "%s"' % connection_name)
        self.session = connections[connection_name]['session']

