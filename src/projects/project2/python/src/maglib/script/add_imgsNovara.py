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
            img.imggroupID.value = 'jpegA'
            img.nomenclature.add_instance().value = "Foto"
            img.sequence_number.set_value(str(i))
            img.usage.add_instance().value = '1'
            file_el = img.file.add_instance()
            file_el.href.value = os.path.join('.', self._base_dir, 'jpegA', f)
            file_el.Location.value = 'URL'


            

    def clean_mag(self, metadigit):
        metadigit.img.clear()
        


    def _imgs_list(self):
        lsdir = os.listdir(os.path.join(self._base_dir, 'jpegA'))
        lsdir.sort()
        return lsdir

    def _get_img_nomenclature(self, fname):
        return os.path.splitext(fname)[0]


if __name__ == '__main__':
    import sys
    m = Main()
    sys.exit(m(sys.argv))
