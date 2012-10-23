"""The heapy handler gives information about the process's memory stack. It is
slow and will block any asynchronous activity and should be used for debugging
purposes only.

For best results, connect directly to the port of the process you would like to
check.

"""
import guppy
import logging
import re
from tornado import web

LOGGER = logging.getLogger(__name__)
MAX_REFERRER_DEPTH = 4
MAX_ROW_COUNT_PER_LEVEL = 5

REPORT_TOTAL = re.compile('^Partition of a set of ([\d]+) objects\.'
                          ' Total size = ([\d]+) bytes\.')
REPORT_HEADER = re.compile('^ Index  Count   %     Size   % Cumulative  % (.*)',
                           re.MULTILINE)
REPORT_ITEMS = re.compile('^\s+([\d]+)\s+([\d]+)\s+([\d]+)\s+([\d]+)\s+'
                          '([\d]+)\s+([\d]+)\s+([\d]+)\s+(.*)', re.MULTILINE)


def get_report_data(heapy_obj, depth=1):
    LOGGER.debug('Getting report data at depth %i', depth)
    report = {'total_objects': 0, 'total_bytes': 0, 'rows': []}
    totals = REPORT_TOTAL.findall(str(heapy_obj))
    if totals:
        report['total_objects'], report['total_bytes'] = (int(totals[0][0]),
                                                          int(totals[0][1]))
    items = REPORT_ITEMS.findall(str(heapy_obj))
    for index, row in enumerate(items):
        report['rows'].append({'item': row[-1],
                               'count': {'value': int(row[1]),
                                         'percent': int(row[2])},
                               'size': {'value': int(row[3]),
                                        'percent': int(row[4])},
                               'cumulative': {'value': int(row[5]),
                                              'percent': int(row[6])}})
        if depth < MAX_REFERRER_DEPTH:
            try:
                rows = len(heapy_obj.byrcs[index])
            except IndexError:
                LOGGER.warning('Could not process item at index %i', index)
                report['rows'][index]['error'] = 'Could not get referrers'
                continue
            if rows > MAX_ROW_COUNT_PER_LEVEL:
                rows = MAX_ROW_COUNT_PER_LEVEL
            for referrer_index in range(0, rows):
                report['rows'][index]['referrers'] =\
                    get_report_data(heapy_obj.byrcs[index].referrers.byrcs,
                                    depth + 1)

    header = REPORT_HEADER.findall(str(heapy_obj))
    if header:
        report['title'] = header[0]
    return report


class HeapyRequestHandler(web.RequestHandler):
    """Dumps the heap to a text/plain output."""

    def initialize(self):
        self._heapy = guppy.hpy()

    def get(self):
        heap = self._heapy.heap()
        report = get_report_data(heap.byrcs)
        self.write(report)
        self.finish()
