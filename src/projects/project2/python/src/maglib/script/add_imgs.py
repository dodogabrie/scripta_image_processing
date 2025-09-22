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
            img.imggroupID.value = 'tiff'
            img.nomenclature.add_instance().value = self._get_img_nomenclature(f)
            img.sequence_number.set_value(str(i))
            img.usage.add_instance().value = '1'
            file_el = img.file.add_instance()
            file_el.href.value = os.path.join('.', self._base_dir, 'tiff', f)
            file_el.Location.value = 'URL'
            altimg = img.altimg.add_instance()
            altimg.imggroupID.value = 'jpeg300'
            altimg.usage.add_instance().value = '2'
            file_el = altimg.file.add_instance()
            file_el.href.value = os.path.join('.', self._base_dir, 'jpeg300', f)
            file_el.Location.value = 'URL'
            altimg = img.altimg.add_instance()
            altimg.imggroupID.value = 'jpeg150'
            altimg.usage.add_instance().value = '3'
            file_el = altimg.file.add_instance()
            file_el.href.value = os.path.join('.', self._base_dir, 'jpeg150', f)
            file_el.Location.value = 'URL'

            

    def clean_mag(self, metadigit):
        metadigit.img.clear()
        


    def _imgs_list(self):
        lsdir = os.listdir(os.path.join(self._base_dir, 'tiff'))
        lsdir.sort()
        return lsdir

    def _get_img_nomenclature(self, fname):
        return os.path.splitext(fname)[0]


if __name__ == '__main__':
    import sys
    m = Main()
    sys.exit(m(sys.argv))
