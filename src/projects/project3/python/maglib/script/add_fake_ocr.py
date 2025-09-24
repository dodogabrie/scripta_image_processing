#!/usr/bin/env python

import re
import random
import time
import hashlib
import os

from maglib.script.common import MagScriptMain, MagOperation
from maglib.utils.misc import iso8601_time


class FakeOcrAdder(MagOperation):
    def do_op(self, metadigit):
        for img in metadigit.img:
            self._add_ocr_for_img(metadigit.ocr, img)

    def clean_mag(self, metadigit):
        metadigit.ocr.clear()

    def _add_ocr_for_img(self, ocr_node, img):
        ocr = ocr_node.add_instance()
        ocr.sequence_number.set_value(img.sequence_number.get_value())
        ocr.nomenclature.set_value(img.nomenclature.get_value())
        ocr.usage.add_instance().value = '3'

        tif_path = img.file[0].href.value
        m = re.match(r'^\./(.*?)/tiff/(.*)\.tif$', tif_path)
        assert m
        pdf_path = './%s/pdf/%s.pdf' % (m.group(1), m.group(2))
        ocr.file.add_instance()
        ocr.file[0].Location.value = 'URI'
        ocr.file[0].href.value = pdf_path

        # Utilizza la vera funzione hash MD5
        ocr.md5.set_value(self._calculate_md5(pdf_path))

        ocr.source.add_instance()
        ocr.source[0].Location.value = 'URI'
        ocr.source[0].href.value = tif_path

        # *** FIX: Gestione del problema di NoneType in filesize ***
        filesize_value = img.filesize.get_value()
        if filesize_value is None:
            print(f"⚠️ Attenzione: il file {tif_path} non ha una dimensione valida. Imposto a 0.")
            filesize_value = 0  # Imposta un valore predefinito per evitare errori

        ocr.filesize.set_value(str(int(filesize_value)))  # Ora non si blocca più

        ocr.format.add_instance()
        ocr.format[0].name.set_value('PDF')
        ocr.format[0].mime.set_value('application/pdf')
        ocr.format[0].compression.set_value('Uncompressed')
        ocr.software_ocr.set_value('ABBYY FineReader 12')

        try:
            tIme = time.strptime(img.datetimecreated.get_value(), '%Y-%m-%dT%H:%M:%SZ')
            t = time.mktime(tIme)
            t += random.randint(100, 3600 * 24 * 30)
            ocr.datetimecreated.set_value(iso8601_time(t))
        except Exception as e:
            print(f"⚠️ Errore nella gestione della data di creazione per {tif_path}: {e}")

    @classmethod
    def _calculate_md5(cls, file_path):
        """ Calcola l'MD5 di un file, verificando che esista """
        if not os.path.exists(file_path):
            print(f"⚠️ Attenzione: il file {file_path} non esiste! Impossibile calcolare MD5.")
            return "00000000000000000000000000000000"  # Valore fittizio per evitare errori

        md5_hash = hashlib.md5()
        with open(file_path, 'rb') as file:
            for chunk in iter(lambda: file.read(4096), b''):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()


class Main(MagScriptMain):
    def _build_mag_operation(self, options, args):
        return FakeOcrAdder()


if __name__ == '__main__':
    import sys
    main = Main()
    sys.exit(main(sys.argv))
