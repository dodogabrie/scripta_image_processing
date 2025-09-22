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
            help=(
                "nome da usare per la directory delle risorse del mag e "
                "come prefisso dei file"
            ),
        )
        self.add_option(
            "--short-filenames",
            action="store_true",
            default=False,
            help="Usa nomi file brevi che includono solo il numero sequenziale",
        )

        self.add_option(
            "--path-style",
            action="store",
            default="default",
            help="Crea i percorsi con questo stile. Supportato: default, fascicle",
        )

        self.add_option(
            "--ignore-missing",
            action="store_true",
            help="Ignora i file mancanti. Il percorso nel MAG sarà modificato.",
        )


class AdaptFs(MagOperation):
    def __init__(
        self,
        base_src_dir,
        base_dst_dir,
        bname=None,
        dry_run=False,
        copy=False,
        short_filenames=False,
        path_style="default",
        ignore_missing=False,
    ):
        self._bname = bname
        self._base_dst_dir = base_dst_dir
        self._base_src_dir = base_src_dir
        self._dry_run = dry_run
        self._copy = copy
        self._short_filenames = short_filenames
        self._path_style = path_style

        if self._dry_run:
            self._transporter = DummyTransporter()
        elif self._copy:
            self._transporter = CopyTransporter(ignore_missing)
        else:
            self._transporter = MoveTransporter(ignore_missing)

    def do_op(self, metadigit):

        bname = self._bname
        if not bname:
            bname = self._guess_bname(metadigit)
        if not bname:
            raise MagOperationError("need identifier to adapt filesystem")

        for i, img_node in enumerate(metadigit.img, 1):
            for img in [img_node] + list(img_node.altimg):
                self._do_file_element(bname, i, img.file[0])

        for i, ocr in enumerate(metadigit.ocr, 1):
            self._do_file_element(bname, i, ocr.file[0])
            if ocr.source:
                self._do_file_element(bname, i, ocr.source[0], False)

    def _do_file_element(self, bname, index, file_el, transport=True):
        origpath = file_el.href.value
        newpath = self._build_new_path(origpath, index, bname)
        file_el.href.value = newpath
        src = normpath(join(self._base_src_dir, origpath))
        dst = normpath(join(self._base_dst_dir, newpath))
        if transport and src != dst:
            self._transporter.transport(src, dst)

    def clean_mag(self, metadigit):
        raise NotImplementedError()

    @property
    def write_mag(self):
        return not self._dry_run

    def _guess_bname(self, metadigit):
        if metadigit.bib and metadigit.bib[0].identifier:
            return metadigit.bib[0].identifier[0].value
        return None

    def _build_new_path(self, origpath, index, bname):
        old_path = MagResourcePath(origpath)

        new_dir = self._build_new_dir(bname, old_path)
        new_filename = self._build_new_filename(old_path, index, bname)
        new_path = f"{new_dir}/{new_filename}"

        return new_path

    def _build_new_dir(self, bname, old_path):
        if self._path_style == "default":
            return str(PurePosixPath(bname) / old_path.resource_dirname)
        if self._path_style == "fascicle":
            m = re.match(
                "^(?P<bid>.+?)" "_" "(?P<year>[0-9]{4})" "(?P<rest>.+)$",
                bname,
            )
            if not m:
                raise MagOperationError(
                    f'Invalid mag basename {bname} for "fascicle" path style'
                )
            return str(
                PurePosixPath(m.group("bid"))
                / m.group("year")
                / (m.group("year") + m.group("rest"))
                / old_path.resource_dirname
            )
        else:
            raise MagOperationError("Invalid path_style")

    def _build_new_filename(self, old_path: MagResourcePath, index, bname) -> str:
        if self._short_filenames:
            file_basename = f"{index:05d}"
        else:
            file_basename = f"{bname}_{index:05d}"
        return f"{file_basename}.{old_path.file_extension}"


class Main(MagScriptMain):
    def _build_opt_parser(self):
        return OptionParser()

    def _build_mag_operation(self, options, args):
        if options.input:
            src_dir = os.path.dirname(options.input)
        else:
            src_dir = os.getcwd()

        if options.base_dst_dir:
            dst_dir = options.base_dst_dir
        elif options.output:
            dst_dir = os.path.dirname(options.output)
        elif options.input:
            dst_dir = os.path.dirname(options.input)
        else:
            dst_dir = os.getcwd()

        bname = options.basename or splitext(basename(options.input))[0]

        return AdaptFs(
            src_dir,
            dst_dir,
            bname,
            options.dry_run,
            options.copy,
            options.short_filenames,
            options.path_style,
            options.ignore_missing,
        )


class FileTransporter(object):
    """classe base astratta per trasportare i file"""

    def transport(self, old_file, new_file):
        raise NotImplementedError()

    def _prepare_dir(self, filepath):
        dir_ = os.path.dirname(filepath)
        if not os.path.isdir(dir_):
            os.makedirs(dir_)


class DummyTransporter(FileTransporter):
    def transport(self, old_path, new_path):
        old_path, new_path = (normpath(p) for p in (old_path, new_path))
        print("%s -> %s" % (old_path, new_path))


class CopyTransporter(FileTransporter):
    def __init__(self, ignore_missing):
        self._ignore_missing = ignore_missing

    def transport(self, old_path, new_path):
        self._prepare_dir(new_path)
        if self._ignore_missing and not os.path.isfile(old_path):
            log.info("ignoring missing file %s", old_path)
            return
        shutil.copy2(old_path, new_path)


class MoveTransporter(FileTransporter):
    def __init__(self, ignore_missing):
        self._ignore_missing = ignore_missing

    def transport(self, old_path, new_path):
        if os.path.isfile(new_path):
            return
        if self._ignore_missing and not os.path.isfile(old_path):
            log.info("ignoring missing file %s", old_path)
            return
        self._prepare_dir(new_path)
        shutil.move(old_path, new_path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    import sys

    main = Main()
    sys.exit(main(sys.argv))
