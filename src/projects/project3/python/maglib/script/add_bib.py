#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from maglib.unimarc_import.base import UnimarcBibAdder, StubVirtualBidTester
from maglib.unimarc_import.mappings.moderno import ModernoMapper
from maglib.script.common import MagScriptMain, MagScriptOptionParser


class OptionParser(MagScriptOptionParser):
    def __init__(self):
        MagScriptOptionParser.__init__(self)
        self.add_option(
            '-u', '--unimarc-dir', action='store', default=None, required=True,
            help='directory con i record unimarc')
        self.set_options_required('--input')
        
class BibAdder(UnimarcBibAdder):
    def _build_mapper(self):
        return ModernoMapper(self._records_retriever, StubVirtualBidTester())


class Main(MagScriptMain):
    def _build_opt_parser(self):
        return OptionParser()
		
    def _build_mag_operation(self, opts, args):
        basename = os.path.splitext(os.path.basename(opts.input))[0]
        bid = basename.split('_')[0]
        return BibAdder(bid, opts.unimarc_dir)

if __name__ == '__main__':
    import sys
    main = Main()
    sys.exit(main(sys.argv))
