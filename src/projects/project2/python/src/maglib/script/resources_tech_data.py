#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""aggiunge le informazioni tecniche sulle risorse riferite dal mag"""

import os
import re

from maglib.script.common import MagScriptMain, MagOperation,\
    MagScriptOptionParser
from maglib.utils.file_md_importer import \
    Img_info_importer, Doc_info_importer, Audio_info_importer, Video_info_importer


class Main(MagScriptMain):
    def _build_mag_operation(self, opts, args):
        if opts.input:
            img_path = os.path.dirname(opts.input)
        else:
            img_path = os.getcwd()
        return TechDataAdder(
            img_path, not opts.recompute_md5,
            not opts.skip_images, not opts.skip_master_images,
            not opts.skip_ocrs, not opts.skip_audio, not opts.skip_video)

    def _build_opt_parser(self):
        return OptionParser()

# TODO: separare logica di esecuzione in classe a se stante dentro
# maglib.utils.file_md_importer, visto che è usata anche da magtool
class TechDataAdder(MagOperation):
    def __init__(self, path, skip_present_md5=True,
                 add_imgs_tech=True, add_master_imgs_tech=True, add_docs_tech=True,
                 add_ocrs_tech=True, add_audio_tech=True, add_video_tech=True):
        self._path = path
        self._img_groups_dict = {}
        self._skip_present_md5 = skip_present_md5
        self._add_imgs_tech = add_imgs_tech
        self._add_master_imgs_tech = add_master_imgs_tech
        self._add_ocrs_tech = add_ocrs_tech
        self._add_docs_tech = add_docs_tech
        self._add_audio_tech = add_audio_tech
        self._add_video_tech = add_video_tech

    def do_op(self, metadigit):
        self._do_imgs(metadigit)
        self._do_ocrs(metadigit)
        self._do_docs(metadigit)
        self._do_audios(metadigit)
        self._do_videos(metadigit)

    def _do_imgs(self, metadigit):
        if not self._add_imgs_tech:
            return
        for img in metadigit.img:
            if self._add_master_imgs_tech:
                Img_info_importer(
                    self._find_img_group(metadigit, img.imggroupID.value),
                    img, self._path, self._calc_md5(img))

            for altimg in img.altimg:
                Img_info_importer(self._find_img_group(
                        metadigit, altimg.imggroupID.value),
                    altimg, self._path, self._calc_md5(altimg))

    def _do_ocrs(self, metadigit):
        if not self._add_ocrs_tech:
            return
        for ocr in metadigit.ocr:
            Doc_info_importer(ocr, self._path, self._calc_md5(ocr))

    def _do_docs(self, metadigit):
        if not self._add_docs_tech:
            return
        for doc in metadigit.doc:
            Doc_info_importer(doc, self._path, self._calc_md5(doc))

    def _do_audios(self, metadigit):
        if not self._add_audio_tech:
            return
        for audio in metadigit.audio:
            for audio_proxy in audio.proxies:
                Audio_info_importer(
                    audio_proxy, self._path, self._calc_md5(audio_proxy))

    def _do_videos(self, metadigit):
        if not self._add_video_tech:
            return
        for video in metadigit.video:
            for video_proxy in video.proxies:
                Video_info_importer(
                    video_proxy, self._path, self._calc_md5(video_proxy))

    def _find_img_group(self, metadigit, iD):
        try:
            return self._img_groups_dict[iD]
        except KeyError:
            pass

        self._img_groups_dict[iD] = None
        if metadigit.gen:
            for img_group in metadigit.gen[0].img_group:
                if img_group.ID.value == iD:
                    self._img_groups_dict[iD] = img_group
                    break

        return self._img_groups_dict[iD]

    def _calc_md5(self, resource):
        # dice se calcolare il codice md5 di una particolare risorsa
        if not self._skip_present_md5:
            return True
        md5 = resource.md5.get_value()
        if not md5 or not re.match('^[0-9a-fA-F]{32}$', md5):
            return True
        return False


class OptionParser(MagScriptOptionParser):
    def __init__(self):
        MagScriptOptionParser.__init__(self)
        self.add_option('-r', '--recompute-md5', action='store_true',
                        default=False,
                        help=u'ricalcola anche gli md5 già presenti')
        self.add_option('-I', '--skip-images', action='store_true',
                        default=False, help='Salta le immagini')
        self.add_option('-m', '--skip-master-images', action='store_true',
                        default=False, help='Salta il formato master '
                        'delle immagini')
        self.add_option('-O', '--skip-ocrs', action='store_true',
                        default=False, help='Salta gli ocr')
        self.add_option('-A', '--skip-audio', action='store_true',
                        default=False, help='salta gli audio')
        self.add_option('-V', '--skip-video', action='store_true',
                        default=False, help='salta i video')


if __name__ == '__main__':
    import sys
    import logging
    logging.basicConfig(level=logging.INFO)
    main = Main()
    sys.exit(main(sys.argv))
