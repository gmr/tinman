#!/usr/bin/env python
"""Will generate a plaintext report from the JSON document created
by the HeapyRequestHandler.

Usage: tinman-heap-report file.json

"""
import json
import os
import sys


def print_row(row, depth):
    prefix = ''.join([' ' for offset in range(0, depth * 4)])
    item = '%s - %s' % (prefix, row['item'])
    parts = [item.ljust(80),
             ('%(value)s' % (row['count'])).rjust(10),
             (' %(percent)s%%' % (row['count'])).rjust(7),
             ('%(value)s' % (row['size'])).rjust(10),
             (' %(percent)s%%' % (row['size'])).rjust(7)]
    print ''.join(parts)


def main():
    if len(sys.argv) == 1 or not (os.path.exists(sys.argv[1]) and
                                  os.path.isfile(sys.argv[1])):
        print 'Usage: tinman-heap-report heap-file.json\n'
        sys.exit(-1)
    with open(sys.argv[1], "r") as handle:
        report = json.load(handle)
    print ''.join(['Item'.ljust(80), 'Count'.rjust(17), 'Size'.rjust(17)])
    print ''.join(['-' for position in xrange(0, 114)])
    for row in report['rows']:
        print
        print_row(row, 0)
        for child in row['referrers']['rows']:
            print
            print_row(child, 1)
            for grandchild in child['referrers']['rows']:
                print_row(grandchild, 2)

if __name__ == '__main__':
    main()
