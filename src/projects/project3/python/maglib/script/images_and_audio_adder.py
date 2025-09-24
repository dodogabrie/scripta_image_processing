#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Questo script consente di importare le risorse all'interno di un mag.
"""

import os
from maglib.script.common import MagOperation, MagScriptMain, MagScriptOptionParser
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
        super().__init__()
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
        opts = VideoImport
