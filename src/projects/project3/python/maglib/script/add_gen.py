#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Importa la sezione gen da un file ini in questa forma

stprog = http://www.braidense.it/
collection = Fondo manzoniano
agency = Biblioteca nazionale Braidense - Milano
access_rights = 1
completeness = 0
"""

from maglib.script.common import MagOperation, MagScriptMain, \
    MagScriptInfoFileOptParser, MagInfoReader, MagOperationError

class GenAdder(MagOperation):
    def __init__(self, info_file):
        """:info_file: file con le informazioni da inserire in <gen>"""
        self._info_file = info_file

    def do_op(self, metadigit):
        info = self._build_info()

        if not metadigit.gen:
            metadigit.gen.add_instance()
        gen = metadigit.gen[0]

        if ('stprog') in info:
            gen.stprog.set_value(info['stprog'])
        if ('agency') in info:
            gen.agency.set_value(info['agency'])
        if ('collection') in info:
            gen.collection.set_value(info['collection'])
        if ('access_rights') in info:
            gen.access_rights.set_value(info['access_rights'])
        if ('completeness') in info:
            gen.completeness.set_value(info['completeness'])

    def clean_mag(self, metadigit):
        if metadigit.gen:
            gen = metadigit.gen[0]
            gen.stprog.clear()
            gen.agency.clear()
            gen.collection.clear()
            gen.access_rights.value = None
            gen.completeness.value = None

    def _build_info(self):
        try:
            return MagInfoReader.read_file(self._info_file)
        except IOError as exc:
            raise MagOperationError(exc)



class Main(MagScriptMain):
    def _build_mag_operation(self, opts, args):
        return GenAdder(opts.info_file)

    def _build_opt_parser(self):
        return MagScriptInfoFileOptParser(
            'file con le informazioni per la sezione gen')


if __name__ == '__main__':
    import sys
    main = Main()
    sys.exit(main(sys.argv))
