#!/usr/bin/env python

import configparser
import os

from lxml import etree

from maglib.mets_export import MetsExporter
from maglib.script.common import (
    MagOperation,
    MagOperationError,
    MagScriptMain,
    MagScriptOptionParser,
)


class Main(MagScriptMain):
    def _build_opt_parser(self):
        return OptionParser()

    def _build_mag_operation(self, options, args):
        if options.mass_mode:
            if not options.output_dir:
                raise MagOperationError("Outputdir required in mass mode")
            output_file = os.path.join(options.output_dir, options.input)
            output = open(output_file, "wb")
        else:
            output = sys.stdout.buffer

        return MetsExport(
            output, options.img_change_history, options.info_file, options.empty_info
        )


class OptionParser(MagScriptOptionParser):
    def __init__(self):
        super(OptionParser, self).__init__()
        self.add_option("-O", "--output-dir", default=None)
        self.add_option(
            "--img-change-history",
            action="store_true",
            help="add ChangeHistory section for derived images",
        )
        self.add_option(
            "-I",
            "--info-file",
            action="store",
            dest="info_file",
            default=None,
            help="file ini con le informazioni per l'export mets",
        )
        self.add_option(
            "--empty-info",
            action="store_true",
            help="Non inserire le informazioni di default",
        )


class MetsExport(MagOperation):
    write_mag = False

    def __init__(self, output_fp, img_change_history, info_file, empty_info):
        self._output_fp = output_fp
        self._img_change_history = img_change_history
        self._info_file = info_file
        self._empty_info = empty_info

    def do_op(self, metadigit):
        if self._empty_info:
            infoparser = configparser.ConfigParser()
        elif self._info_file:
            infoparser = configparser.ConfigParser()
            infoparser.read(self._info_file)
        else:
            infoparser = None

        exporter = MetsExporter(metadigit, self._img_change_history, infoparser)
        exporter.convert()

        mets = etree.ElementTree(exporter.mets)

        mets.write(
            self._output_fp, pretty_print=True, xml_declaration=True, encoding="utf-8"
        )


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.DEBUG)
    import sys

    main = Main()
    sys.exit(main(sys.argv))
