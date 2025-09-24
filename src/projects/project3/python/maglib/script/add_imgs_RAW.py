#!/usr/bin/env python

import os
from maglib.script.common import MagScriptMain, MagOperation


class Main(MagScriptMain):
    def _build_mag_operation(self, options, args):
        d = os.path.splitext(options.input)[0]
        return ImagesAdder(d)


class ImagesAdder(MagOperation):
    def __init__(self, base_dir):
        self._base_dir = base_dir

    def do_op(self, metadigit):
        lsdir = self._imgs_list()
        for i, f in enumerate(lsdir, 1):
            img = metadigit.img.add_instance()
            img.imggroupID.value = 'raw'
            img.nomenclature.add_instance().value = self._get_img_nomenclature(f)
            img.sequence_number.set_value(str(i))
            img.usage.add_instance().value = '0'
            file_el = img.file.add_instance()
            file_el.href.value = os.path.join('.', self._base_dir, 'RAW', f)
            file_el.Location.value = 'URL'
            
            tiff_file = f.replace('.dng', '.tif')
            if os.path.exists(os.path.join(self._base_dir, 'TIFF', tiff_file)):
                altimg = img.altimg.add_instance()
                altimg.imggroupID.value = 'tiff'
                altimg.usage.add_instance().value = '1'
                file_el = altimg.file.add_instance()
                file_el.href.value = os.path.join('.', self._base_dir, 'TIFF', tiff_file)
                file_el.Location.value = 'URL'
            
            jpeg300_file = f.replace('.dng', '.jpg')
            if os.path.exists(os.path.join(self._base_dir, 'JPEG', jpeg300_file)):
                altimg = img.altimg.add_instance()
                altimg.imggroupID.value = 'jpeg300'
                altimg.usage.add_instance().value = '2'
                file_el = altimg.file.add_instance()
                file_el.href.value = os.path.join('.', self._base_dir, 'JPEG', jpeg300_file)
                file_el.Location.value = 'URL'


    def clean_mag(self, metadigit):
        metadigit.img.clear()

    def _imgs_list(self):
        raw_dir = os.path.join(self._base_dir, 'RAW')
        return sorted([f for f in os.listdir(raw_dir) if f.lower().endswith('.dng')])

    def _get_img_nomenclature(self, fname):
        return os.path.splitext(fname)[0]


if __name__ == '__main__':
    import sys
    m = Main()
    sys.exit(m(sys.argv))
