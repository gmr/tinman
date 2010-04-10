"""
Common Model Parts
"""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects import postgresql

# Use declaritive base syntax
Base = declarative_base()

# metadata object for this module
metadata = Base.metadata