#!/usr/bin/env python
# -*- coding: utf-8 -*-

from maglib.script.common import MagOperation, MagScriptMain, \
    MagScriptOptionParser


class VoidOperation(MagOperation):
    def do_op(self, metadigit):
        pass


class OptionParser(MagScriptOptionParser):
    def __init__(self, *args, **kwargs):
        MagScriptOptionParser.__init__(self, *args, **kwargs)
        self.remove_option('--clean')


class Main(MagScriptMain):
    def _build_mag_operation(self, options, args):
        return VoidOperation()

    def _build_opt_parser(self):
        return OptionParser()


if __name__ == '__main__':
    import sys
    m = Main()
    sys.exit(m(sys.argv))

