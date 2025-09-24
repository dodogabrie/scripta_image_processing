#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""stampa i record MARC da file o dallo standard input"""

from __future__ import print_function

import sys

from pymarc import MARCReader

if sys.version_info[0] == 2:
    string_type = unicode       # noqa
else:
    string_type = str


def print_records(f):
    reader = MARCReader(f, force_utf8=0)
    for record in reader:
        print('=LDR  %s' % record.leader)
        for f in record.fields:
            f = string_type(f)
            print(f.encode('utf-8'))
        print()
        # print record


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print_records(sys.stdin)
    else:
        for filename in sys.argv[1:]:
            if filename == '-':
                print_records(sys.stdin)
            else:
                try:
                    f = open(filename, 'rb')
                except IOError as exc:
                    sys.stderr.write('Can\'t open %s: %s\n' % (filename, exc))
                    sys.exit(1)
            print_records(f)
