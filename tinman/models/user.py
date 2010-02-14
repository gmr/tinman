#!/usr/bin/env python
"""
Tinman Authentication Models
"""

__author__  = "Gavin M. Roy"
__email__   = "gavinmroy@gmail.com"
__date__    = "2010-02-13"
__version__ = 0.1

from tinman.data import Model

class User(Model):

    username = Model.Column('username', Model.String(20))
    email = Model.Column('email', Model.String(255))
    password = Model.Column('password', Model.String(32))