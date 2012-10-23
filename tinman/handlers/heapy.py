"""The heapy handler gives information about the process's memory stack. It is
slow and will block any asynchronous activity and should be used for debugging
purposes only.

For best results, connect directly to the port of the process you would like to
check.

"""
import guppy
import re
from tornado import web

REPORT_TOTAL = re.compile('^Partition of a set of ([\d]+) objects\.'
                          ' Total size = ([\d]+) bytes\.')
REPORT_HEADER = re.compile('^ Index  Count   %     Size   % Cumulative  % (.*)',
                           re.MULTILINE)
REPORT_ITEMS = re.compile('^\s+([\d]+)\s+([\d]+)\s+([\d]+)\s+([\d]+)\s+'
                          '([\d]+)\s+([\d]+)\s+([\d]+)\s+(.*)', re.MULTILINE)


def get_report_data(heapy_obj):
    report = {'total_objects': 0, 'total_bytes': 0, 'rows': []}
    totals = REPORT_TOTAL.findall(str(heapy_obj))
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
        rows = len(heap.byrcs)
        for index in range(0, 10 if rows > 10 else rows):
            report['rows'][index]['referrers'] = \
                get_report_data(heap.byrcs[index].referrers.byrcs)
        self.write(report)
        self.finish()


if __name__ == '__main__':

    heapy = guppy.hpy()
    heap = heapy.heap()
    report = get_report_data(heap.byrcs)
    rows = len(heap.byrcs)
    for index in range(0, 10 if rows > 10 else rows):
        report['rows'][index]['referrers'] = \
            get_report_data(heap.byrcs[index].referrers.byrcs)
    print report
