#!/usr/bin/env python

import os
from maglib.script.common import MagScriptMain, MagOperation

class Main(MagScriptMain):
    def _build_mag_operation(self, options, args):
        base_dir = os.path.splitext(options.input)[0]
        return AudioAdder(base_dir)

class AudioAdder(MagOperation):
    def __init__(self, base_dir):
        self._base_dir = base_dir

    def do_op(self, metadigit):
        audio_files = self._get_audio_files()
        for i, file_name in enumerate(audio_files, 1):
            file_path = os.path.join(self._base_dir, 'wav', file_name)
            
            # Aggiungi elemento audio
            audio = metadigit.audio.add_instance()

            # Sequence number
            audio.sequence_number.set_value(str(i))

            # Nomenclature
            audio.nomenclature.set_value("brano")

            # Proxies
            proxy = audio.proxies.add_instance()
            file_el = proxy.file.add_instance()  # Creazione di un'istanza di file
            
            # Imposta gli attributi usando il metodo corretto
            file_el.href.value = f"./{self._base_dir}/wav/{file_name}"
            file_el.Location.value = "URI"

    def clean_mag(self, metadigit):
        metadigit.audio.clear()

    def _get_audio_files(self):
        """Ottiene la lista dei file audio nella directory wav."""
        audio_dir = os.path.join(self._base_dir, 'wav')
        files = [f for f in os.listdir(audio_dir) if f.lower().endswith('.wav')]
        files.sort()
        return files

if __name__ == '__main__':
    import sys
    m = Main()
    sys.exit(m(sys.argv))
