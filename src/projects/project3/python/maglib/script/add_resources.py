#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
questo script permette di importare le risorse all'interno di un mag"""

import os

from maglib.script.common import MagOperation, MagScriptMain, \
    MagScriptOptionParser
from maglib.utils.resources_import.wizard import (
    ImageImportOptions, ImageImportRunner,
    DocImportOptions, DocImportRunner,
    OcrImportOptions, OcrImportRunner,
    AudioImportOptions, AudioImportRunner,
    VideoImportOptions, VideoImportRunner
)


# TODO: permettere di specificare sottodirectory per ocr, doc, video, audio
# TODO: importazione formati alternativi per video e audio

class ResourcesAdder(MagOperation):
    def __init__(self, resources_path, imgs_master, imgs_alt,
                 dotslash=True, extra_path_levels=1, sort=True,
                 create_img_groups=True,
                 types=('img', 'ocr', 'doc', 'audio', 'video')):
        super(ResourcesAdder, self).__init__()
        self._resources_path = resources_path
        self._imgs_master = imgs_master
        self._imgs_alt = imgs_alt
        self._dotslash = dotslash
        self._extra_path_levels = extra_path_levels
        self._sort = sort
        self._create_img_groups = create_img_groups

        self._types = types

    def do_op(self, metadigit):
        if 'img' in self._types:
            self._add_images(metadigit)
        if 'ocr' in self._types:
            self._add_ocr(metadigit)
        if 'doc' in self._types:
            self._add_doc(metadigit)
        if 'audio' in self._types:
            self._add_audio(metadigit)
        if 'video' in self._types:
            self._add_video(metadigit)

    def clean_mag(self, metadigit):
        if 'img' in self._types:
            metadigit.img.clear()
        if 'ocr' in self._types:
            metadigit.ocr.clear()
        if 'doc' in self._types:
            metadigit.doc.clear()
        if 'audio' in self._types:
            metadigit.audio.clear()
        if 'video' in self._types:
            metadigit.video.clear()

    def _add_images(self, metadigit):
        opts = ImageImportOptions(
            alt_subdirs=self._imgs_alt, create_groups=self._create_img_groups,
            subdirs=self._imgs_master, **self._common_import_opts_args())
        runner = ImageImportRunner(metadigit, self._resources_path, opts)
        runner.run()

    def _add_ocr(self, metadigit):
        opts = OcrImportOptions(
            subdirs=('ocr',), **self._common_import_opts_args())
        runner = OcrImportRunner(metadigit, self._resources_path, opts)
        runner.run()

    def _add_doc(self, metadigit):
        opts = DocImportOptions(
            subdirs=('doc', 'pdf', 'txt'), **self._common_import_opts_args())
        runner = DocImportRunner(metadigit, self._resources_path, opts)
        runner.run()

    def _add_audio(self, metadigit):
        opts = AudioImportOptions(
            subdirs=('audio',), **self._common_import_opts_args())
        runner = AudioImportRunner(metadigit, self._resources_path, opts)
        runner.run()

    def _add_video(self, metadigit):
        opts = VideoImportOptions(
            subdirs=('video',), **self._common_import_opts_args())
        runner = VideoImportRunner(metadigit, self._resources_path, opts)
        runner.run()

    def _common_import_opts_args(self):
        return {
            'sort': self._sort, 'dotslash': self._dotslash,
            'extra_path_levels': self._extra_path_levels
        }


class OptionParser(MagScriptOptionParser):
    def __init__(self):
        MagScriptOptionParser.__init__(self)
        self.add_option(
            '-p', '--extra-path-levels', type='int', action='store', default=1,
            help=('numero di livelli di directory ulteriori nei path '
                  'delle risorse nel mag'))
        self.add_option(
            '-d', '--dir', action='store',
            help='directory che contiene le risorse del mag')
        self.add_option(
            '-I', '--skip-images', action='store_true',
            help='non importare le immagini')
        self.add_option(
            '-O', '--skip-ocr', action='store_true',
            help='non importare gli ocr')
        self.add_option(
            '-D', '--skip-doc', action='store_true',
            help='non importare i doc')
        self.add_option(
            '-A', '--skip-audio', action='store_true',
            help='non importare gli audio')
        self.add_option(
            '-V', '--skip-video', action='store_true',
            help='non importare i video')
        self.add_option(
            '--imgs-master', action='append', default=['tiff'],
            help=('nome sottodirectory in cui cercare le immagini master;'
                  ' supporta la sintassi "glob" della shell'))
        self.add_option(
            '--imgs-alt', action='append', default=['jpeg*', 'thumbs'],
            help=('nome sottodirectory in cui cercare le immagini master;'
                  ' supporta la sintassi "glob" della shell'))
        self.add_option(
            '--no-dotslash', action='store_false', dest='dotslash', default=True,
            help='non inserire "./" prima del nome dei file')
        self.add_option(
            '-C', '--create-img-groups', action='store_false', default=True,
            help='non creare i gruppi di immagini')


class Main(MagScriptMain):
    def _build_mag_operation(self, opts, args):
        if opts.dir:
            d = opts.dir
        elif opts.input:
            d = os.path.splitext(opts.input)[0]
        else:
            d = os.getcwd()

        types = []
        if not opts.skip_images:
            types.append('img')
        if not opts.skip_ocr:
            types.append('ocr')
        if not opts.skip_doc:
            types.append('doc')
        if not opts.skip_audio:
            types.append('audio')
        if not opts.skip_video:
            types.append('video')

        return ResourcesAdder(
            d, opts.imgs_master, opts.imgs_alt, opts.dotslash,
            opts.extra_path_levels, True, opts.create_img_groups, types)

    def _build_opt_parser(self):
        return OptionParser()

if __name__ == '__main__':
    import sys
    import logging
    logging.basicConfig(level=logging.WARN)
    main = Main()
    sys.exit(main(sys.argv))
