#!/usr/bin/env python
# -*- coding: utf-8 -*-

import collections

from maglib import Metadigit
from maglib.script.common import (
    MagScriptMain, MagScriptInfoFileOptParser, BibAdder)
from maglib.utils.misc import BibInfo


class CopyBib(BibAdder):
    def __init__(self, src_mag, skip_fields=()):
        self._src_mag = Metadigit(src_mag)
        self._skip_fields = skip_fields

    def do_op(self, metadigit):
        super(CopyBib, self).do_op(metadigit)
        if self._src_mag.bib:
            bib = self._src_mag.bib[0]
            for holdings in bib.holdings:
                metadigit.bib[0].holdings.append(holdings.copy())

            if not metadigit.bib[0].piece and bib.piece:
                metadigit.piece.append(bib.piece[0].copy())

    def _build_bib_info(self):
        info = collections.defaultdict(list)
        if not self._src_mag.bib:
            return

        for dc_field_name in BibInfo.dc_keys:
            if dc_field_name in self._skip_fields:
                continue
            for field in getattr(self._src_mag.bib[0], dc_field_name):
                info[dc_field_name].append(field.value)
        if self._src_mag.bib[0].level.value:
            info['level'] = self._src_mag.bib[0].level.value

        return info


class OptionParser(MagScriptInfoFileOptParser):
    def __init__(self):
        MagScriptInfoFileOptParser.__init__(self, 'mag sorgente')
        self.add_option(
            '-f', '--skip-fields', action='store', default='',
            help='Campi (separati da virgola) da non importare')


class Main(MagScriptMain):
    def _build_opt_parser(self):
        return OptionParser()

    def _build_mag_operation(self, options, args):
        skip_fields = filter(None, options.skip_fields.split(','))
        return CopyBib(options.info_file, skip_fields)


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)
    import sys
    main = Main()
    sys.exit(main(sys.argv))
