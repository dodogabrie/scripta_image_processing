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


class OptionParser(MagScriptOptionParser):
    def __init__(self):
        MagScriptOptionParser.__init__(self)
        self.remove_option("-c")
        self.add_option(
            "-d",
            "--base-dst-dir",
            action="store",
            help="Directory base dove copiare i file",
        )
        self.add_option(
            "-s",
            "--base-src-dir",
            action="store",
            help="Directory base da cui copiare i file",
        )
        self.add_option(
            "-n",
            "--dry-run",
            action="store_true",
            help="Non effettuare nessun spostamento, stampa solo",
        )
        self.add_option(
            "-C", "--copy", action="store_true", help="Copia invece di spostare"
        )
        self.add_option(
            "-b",
            "--basename",
            action="store",
            help="Nome della pubblicazione",
        )
        self.add_option(
            "--ignore-missing",
            action="store_true",
            help="Ignora i file mancanti senza interrompere il processo",
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

        if self._dry_run:
            self._transporter = DummyTransporter()
        elif self._copy:
            self._transporter = CopyTransporter(ignore_missing)
        else:
            self._transporter = MoveTransporter(ignore_missing)

    def do_op(self, metadigit):
        year, month, day, fascicolo, edition_suffix = self._extract_bib_info(metadigit)
        bname = self._bname or "UnknownPublication"

        for i, img_node in enumerate(metadigit.img, 1):
            for img in [img_node] + list(img_node.altimg):
                self._do_file_element(bname, year, month, day, fascicolo, edition_suffix, i, img.file[0])

        for i, ocr in enumerate(metadigit.ocr, 1):
            self._do_file_element(bname, year, month, day, fascicolo, edition_suffix, i, ocr.file[0])
            if ocr.source:
                self._do_file_element(bname, year, month, day, fascicolo, edition_suffix, i, ocr.source[0])

    def _extract_bib_info(self, metadigit):
        """ Estrai anno, mese, giorno, numero del fascicolo e il tipo di edizione dall'XML """
        year, month, day, fascicolo, edition_suffix = "0000", "00", "00", "0000", ""

        if metadigit.bib and metadigit.bib[0].piece:
            piece = metadigit.bib[0].piece[0]

            year = str(piece.year[0].value) if piece.year and piece.year[0] else "0000"

            # Estrarre il numero del fascicolo corretto
            issue_str = str(piece.issue[0].value) if piece.issue and piece.issue[0] else ""
            
            # Cerca "fasc. XXX" per estrarre il numero corretto
            fascicolo_match = re.search(r'fasc\. (\d+)', issue_str)
            if fascicolo_match:
                fascicolo = fascicolo_match.group(1).zfill(4)
            else:
                fascicolo = "0000"  # Se non trovato, valore predefinito

            # Identificare "bis", "ter", "suppl" e convertirli in suffissi corretti
            edition_suffix = ""
            if re.search(r'\bbis\b', issue_str, re.IGNORECASE):
                edition_suffix = "_02"
            elif re.search(r'\bter\b', issue_str, re.IGNORECASE):
                edition_suffix = "_03"
            elif re.search(r'\bsuppl\b', issue_str, re.IGNORECASE):
                edition_suffix = "_suppl"

            # Estrarre la data (anno, mese, giorno)
            stpiece_per = str(piece.stpiece_per[0].value) if piece.stpiece_per and piece.stpiece_per[0] else ""
            date_match = re.search(r'\((\d{4})(\d{2})(\d{2})\)', stpiece_per)
            if date_match:
                year, month, day = date_match.groups()

        return year, month, day, fascicolo, edition_suffix

    def _do_file_element(self, bname, year, month, day, fascicolo, edition_suffix, index, file_el):
        origpath = file_el.href.value
        newpath = self._build_new_path(origpath, bname, year, month, day, fascicolo, edition_suffix, index)
        file_el.href.value = newpath

        src = normpath(join(self._base_src_dir, origpath))
        dst = normpath(join(self._base_dst_dir, newpath))
        if src != dst:
            self._transporter.transport(src, dst)

    def _build_new_path(self, origpath, bname, year, month, day, fascicolo, edition_suffix, index):
        old_path = MagResourcePath(origpath)
        new_dir = f"{year}/{month}/{fascicolo}{edition_suffix}"
        new_filename = f"{bname}_{day}_{month}_{year}{edition_suffix}_{index:04d}.{old_path.file_extension}"
        return f"{new_dir}/{new_filename}"


class Main(MagScriptMain):
    def _build_opt_parser(self):
        return OptionParser()

    def _build_mag_operation(self, options, args):
        src_dir = options.base_src_dir or os.getcwd()
        dst_dir = options.base_dst_dir or os.getcwd()
        bname = options.basename or "UnknownPublication"

        return AdaptFs(
            src_dir,
            dst_dir,
            bname,
            options.dry_run,
            options.copy,
            options.ignore_missing,
        )


class FileTransporter:
    def transport(self, old_file, new_file):
        raise NotImplementedError()

    def _prepare_dir(self, filepath):
        dir_ = os.path.dirname(filepath)
        if not os.path.isdir(dir_):
            os.makedirs(dir_, exist_ok=True)


class DummyTransporter(FileTransporter):
    def transport(self, old_path, new_path):
        print(f"Simulazione spostamento: {old_path} -> {new_path}")


class CopyTransporter(FileTransporter):
    def __init__(self, ignore_missing=False):
        self._ignore_missing = ignore_missing

    def transport(self, old_path, new_path):
        self._prepare_dir(new_path)
        if self._ignore_missing and not os.path.isfile(old_path):
            log.warning(f"File mancante: {old_path}, ignorato")
            return
        shutil.copy2(old_path, new_path)


class MoveTransporter(FileTransporter):
    def __init__(self, ignore_missing=False):
        self._ignore_missing = ignore_missing

    def transport(self, old_path, new_path):
        if os.path.isfile(new_path):
            return
        self._prepare_dir(new_path)
        if os.path.isfile(old_path):
            shutil.move(old_path, new_path)
        elif self._ignore_missing:
            log.warning(f"File mancante: {old_path}, ignorato")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    import sys

    main = Main()
    sys.exit(main(sys.argv))
