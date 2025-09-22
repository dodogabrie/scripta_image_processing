#!/usr/bin/env python

import logging
import os
import re
import shutil
from os.path import basename, join, normpath, splitext
from pathlib import PurePosixPath

from maglib.script.common import (
    MagOperation,
    MagOperationError,
    MagScriptMain,
    MagScriptOptionParser,
)
from maglib.utils.misc import MagResourcePath

log = logging.getLogger(__name__)

# Dizionario delle abbreviazioni per le nomenclature
ABBREVIAZIONI_NOMENCLATURE = {
    "Scheda": "S",
    "Foto": "F",
    "Allegato": "A",
    "Disegno": "D",
}

class OptionParser(MagScriptOptionParser):
    def __init__(self):
        MagScriptOptionParser.__init__(self)
        self.remove_option("-c")
        self.add_option(
            "-d",
            "--base-dst-dir",
            action="store",
            help="directory base dove copiare i file",
        )
        self.add_option(
            "-s",
            "--base-src-dir",
            action="store",
            help="directory base da cui copiare i file",
        )
        self.add_option(
            "-n",
            "--dry-run",
            action="store_true",
            help="non effettuare nessun spostamento, stampa",
        )
        self.add_option(
            "-C", "--copy", action="store_true", help="copia invece di spostare"
        )
        self.add_option(
            "-b",
            "--basename",
            action="store",
            help="Nome base da usare per la directory delle risorse e i file",
        )
        self.add_option(
            "--ignore-missing",
            action="store_true",
            default=False,
            help="Ignora i file mancanti durante lo spostamento o la copia",
        )

class AdaptFs(MagOperation):
    def __init__(
        self,
        base_src_dir,
        base_dst_dir,
        bname=None,
        dry_run=False,
        copy=False,
        ignore_missing=False,
    ):
        self._bname = bname
        self._base_dst_dir = base_dst_dir
        self._base_src_dir = base_src_dir
        self._dry_run = dry_run
        self._copy = copy
        self._ignore_missing = ignore_missing

        self._scheda_counter = 0  
        self._category_counters = {abbr: 0 for abbr in ABBREVIAZIONI_NOMENCLATURE.values()}
        self._internal_counters = {abbr: 0 for abbr in ABBREVIAZIONI_NOMENCLATURE.values()}
        self._current_scheda = None

        if self._dry_run:
            self._transporter = DummyTransporter()
        elif self._copy:
            self._transporter = CopyTransporter(self._ignore_missing)
        else:
            self._transporter = MoveTransporter(self._ignore_missing)

    def do_op(self, metadigit):
        bname = self._bname or self._guess_bname(metadigit)
        if not bname:
            raise MagOperationError("Serve un identificatore per adattare il filesystem.")

        for img_node in metadigit.img:
            nomenclature = img_node.nomenclature[0].value
            nomenclature_short = self._get_nomenclature_short(nomenclature)

            if nomenclature_short == "S":
                self._scheda_counter += 1
                self._category_counters = {abbr: 0 for abbr in ABBREVIAZIONI_NOMENCLATURE.values()}
                self._internal_counters = {abbr: 0 for abbr in ABBREVIAZIONI_NOMENCLATURE.values()}
                self._current_scheda = self._scheda_counter
            
            if nomenclature_short != "S":
                self._category_counters[nomenclature_short] += 1
            
            self._internal_counters[nomenclature_short] += 1

            for img in [img_node] + list(img_node.altimg):
                self._do_file_element(
                    bname, self._current_scheda, self._category_counters[nomenclature_short], self._internal_counters[nomenclature_short], nomenclature_short, img.file[0]
                )

    def _do_file_element(self, bname, scheda_number, category_number, sub_index, nomenclature_short, file_el):
        origpath = file_el.href.value
        extension = origpath.split('.')[-1].lower()
        subfolder = "tiff" if "tiff" in origpath else "jpeg300" if "jpeg300" in origpath else ""

        newpath = self._build_new_path(
            scheda_number, category_number, sub_index, bname, nomenclature_short, subfolder, extension
        )
        file_el.href.value = newpath
        src = normpath(join(self._base_src_dir, origpath))
        dst = normpath(join(self._base_dst_dir, newpath))
        self._transporter.transport(src, dst)

    def _build_new_path(self, scheda_number, category_number, sub_index, bname, nomenclature_short, subfolder, extension):
        new_dir = f"{bname}/{subfolder}"
        new_filename = self._build_new_filename(scheda_number, category_number, sub_index, bname, nomenclature_short, extension)
        return f"{new_dir}/{new_filename}"

    def _build_new_filename(self, scheda_number, category_number, sub_index, bname, nomenclature_short, extension):
        return f"{bname}-{scheda_number:04d}_{nomenclature_short}{category_number:04d}_{sub_index:02d}.{extension}"


    def clean_mag(self, metadigit):
        raise NotImplementedError()		

    @property
    def write_mag(self):
        return not self._dry_run

    def _guess_bname(self, metadigit):
        if metadigit.bib and metadigit.bib[0].identifier:
            return metadigit.bib[0].identifier[0].value
        return None

    def _get_nomenclature_short(self, nomenclature):
        for key in ABBREVIAZIONI_NOMENCLATURE:
            if key in nomenclature:
                return ABBREVIAZIONI_NOMENCLATURE[key]
        return "X"

class FileTransporter(object):
    def transport(self, old_file, new_file):
        raise NotImplementedError()

    def _prepare_dir(self, filepath):
        dir_ = os.path.dirname(filepath)
        if not os.path.isdir(dir_):
            os.makedirs(dir_)

class DummyTransporter(FileTransporter):
    def transport(self, old_path, new_path):
        print(f"{normpath(old_path)} -> {normpath(new_path)}")

class CopyTransporter(FileTransporter):
    def __init__(self, ignore_missing):
        self._ignore_missing = ignore_missing

    def transport(self, old_path, new_path):
        self._prepare_dir(new_path)
        if self._ignore_missing and not os.path.isfile(old_path):
            log.warning(f"Ignorando file mancante: {old_path}")
            return
        shutil.copy2(old_path, new_path)

class MoveTransporter(FileTransporter):
    def __init__(self, ignore_missing):
        self._ignore_missing = ignore_missing

    def transport(self, old_path, new_path):
        self._prepare_dir(new_path)
        if self._ignore_missing and not os.path.isfile(old_path):
            log.warning(f"Ignorando file mancante: {old_path}")
            return
        shutil.move(old_path, new_path)

class Main(MagScriptMain):
    def _build_opt_parser(self):
        return OptionParser()

    def _build_mag_operation(self, options, args):
        src_dir = options.base_src_dir or os.getcwd()
        dst_dir = options.base_dst_dir or os.getcwd()
        bname = options.basename or splitext(basename(options.input))[0]
        return AdaptFs(src_dir, dst_dir, bname, options.dry_run, options.copy, options.ignore_missing)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    import sys
    main = Main()
    sys.exit(main(sys.argv))


