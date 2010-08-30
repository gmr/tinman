#!/usr/bin/env python
"""
Tinman Data Layer
"""

__author__  = "Gavin M. Roy"
__email__   = "gavinmroy@gmail.com"
__date__    = "2010-02-07"
__version__ = 0.3

import logging

# A persistent dictionary for our database connection and elements
connections = {}

class DataLayer:

    active = None
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
                    if not connections.has_key(connection['name']):
                        connections[connection['name']] = {'driver': connection['driver']}
                        logging.debug('Creating new SQLAlchemy engine instance')
                        connections[connection['name']]['engine'] = sqlalchemy.create_engine(connection['dsn'])
                        session = sqlalchemy.orm.sessionmaker(bind=connections[connection['name']]['engine'], autocommit=True, autoflush=True)
                        connections[connection['name']]['session'] = session()
                        connections[connection['name']]['metadata'] = sqlalchemy.MetaData(bind=connections[connection['name']]['engine'])
                        if not self.session:
                            logging.debug('Setting default session to "%s"' % connection['name'])
                            self.session = connections[connection['name']]['session']
                elif connection['driver'] == 'psycopg2':
                    import psycopg2
                    import psycopg2.extras
                    if not connections.has_key(connection['dbname']):                    
                        connections[connection['dbname']] = {'driver': connection['driver']}
                        dsn = []
                        if connection.has_key('host'):
                          dsn.append("host='%s'" % connection['host'])
                        if connection.has_key('port'):
                          dsn.append("port='%i'" % connection['port'])
                        if connection.has_key('username'):
                          dsn.append("user='%s'" % connection['username'])
                        if connection.has_key('password'):
                          dsn.append("password='%s'" % connection['password'])
                        if connection.has_key('dbname'):
                          dsn.append("dbname='%s'" % connection['dbname'])
                        dsn_string = ' '.join(dsn)
                        logging.debug('Creating new psycopg2 instance connecting to "%s"' % dsn_string)
                        try:
                            connections[connection['dbname']]['connection'] = psycopg2.connect(dsn_string)
                        except psycopg2.OperationalError, e:
                            logging.error("Error connecting to the PostgreSQL database \"%s\": %s" % (connection['dbname'], e[0]))
                            continue
                            
                        connections[connection['dbname']]['connection'].set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
                        connections[connection['dbname']]['cursor'] = connections[connection['dbname']]['connection'].cursor(cursor_factory=psycopg2.extras.DictCursor)
                else:
                    logging.error('Unknown data driver type')
            else:
                logging.error('Connection is missing the driver setting')

    def set_active_connection(self, connection_name):
        global connections
        logging.debug('Setting active connection to "%s"' % connection_name)
        self.active = connections[connection_name]

        self.active = connections[connection_name]

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

    def commit(self, connection_name=None):
        global connections
        if connection_name:
            logging.debug('Committing connection "%s"' % connection_name)
            connections[connection_name]['session'].commit()
        else:
            for connection in connections:
                if connections[connection]['driver'] == 'SQLAlchemy':
                    if connections[connection]['session'].dirty:
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

