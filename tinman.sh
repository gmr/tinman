#!/usr/bin/python
# EASY-INSTALL-ENTRY-SCRIPT: 'tinman','console_scripts','tinman'
__requires__ = 'tinman'
import sys
sys.path.insert(0, '/Users/gmr/Source/Tinman/')
from pkg_resources import load_entry_point

sys.exit(
   load_entry_point('tinman', 'console_scripts', 'tinman')()
)
