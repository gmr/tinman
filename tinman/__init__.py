#!/usr/bin/env python
"""
Core Tinman imports
"""
__author__ = 'Gavin M. Roy'
__email__ = '<gmr@myyearbook.com>'
__since__ = '2011-03-14'
__version__ = "0.2.8"

__all__ = ['tinman.application',
           'tinman.cache',
           'tinman.cli',
           'tinman.clients',
           'tinman.utils',
           'tinman.whitelist']

def main(*args):

    # Import our CLI parser
    from tinman import cli

    # Run the main routine
    process = cli.TinmanProcess()
    process.run()

if __name__ == "__main__":

    # Run our CLI process
    main()
