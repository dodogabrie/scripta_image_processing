#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from maglib.csv_import import CsvBibInfoCreator
from maglib.script.common import MagScriptMain, MagScriptInfoFileOptParser, \
    BibAdder, MagOperationError



class Main(MagScriptMain):
    def _build_opt_parser(self):
        return OptionParser()
    def _build_mag_operation(self, options, args):
        return CsvBibAdder(
            options.info_file, options.identifier_field,
            os.path.splitext(os.path.basename(options.input))[0])

class OptionParser(MagScriptInfoFileOptParser):
    def __init__(self):
        MagScriptInfoFileOptParser.__init__(self,'file csv con i dati bibliografici')
        self.add_option(
            '-f', '--identifier-field', action='store', default='identifier',
            help='Nome del campo per identificare il record del mag, '
            'se diverso da identifier')


class CsvBibAdder(BibAdder):
    def __init__(self, csv_file, identifier_field, mag_identifier):
        self._csv_file = csv_file
        self._bib_info_creator = CsvBibInfoCreator(identifier_field)
        self._mag_identifier = mag_identifier

    def _build_bib_info(self):
        self._bib_info_creator.read_file(self._csv_file)
        bib_info = self._bib_info_creator.get_info(self._mag_identifier)
        if not bib_info:
            raise MagOperationError(
                'impossibile trovare info per il mag %s' % self._mag_identifier)
        return bib_info


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)
    import sys
    main = Main()
    sys.exit(main(sys.argv))
