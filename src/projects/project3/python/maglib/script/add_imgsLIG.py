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
            # Impostazione del valore di sequence_number
            sequence_number = img.sequence_number.add_instance()
            sequence_number.value = str(i)

            # Creare e impostare l'elemento 'usage'
            usage = img.usage.add_instance()
            usage.value = '1'
            
            # Aggiungere il 'nomenclature'
            nomenclature = img.nomenclature.add_instance()
            nomenclature.value = self._get_img_nomenclature(f)

            # Creare e impostare l'elemento 'file'
            file_el = img.file.add_instance()
            file_el.href.value = os.path.join('.', self._base_dir, 'tiff', f)
            file_el.Location.value = 'URI'

            # Creare e impostare l'elemento 'altimg' per jpeg300
            altimg_300 = img.altimg.add_instance()
            usage_300 = altimg_300.usage.add_instance()
            usage_300.value = '2'
            file_el_300 = altimg_300.file.add_instance()
            file_el_300.href.value = os.path.join('.', self._base_dir, 'jpeg300', f)
            file_el_300.Location.value = 'URI'

            # Creare e impostare l'elemento 'altimg' per jpeg150
            altimg_150 = img.altimg.add_instance()
            usage_150 = altimg_150.usage.add_instance()
            usage_150.value = '3'
            file_el_150 = altimg_150.file.add_instance()
            file_el_150.href.value = os.path.join('.', self._base_dir, 'jpeg150', f)
            file_el_150.Location.value = 'URI'

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
