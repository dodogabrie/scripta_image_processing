#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import sys
import pymarc


class Record(object):
    def __init__(self, marc_record):
        self._marc_record = marc_record

    def write(self, filepath):
        with open(filepath, 'wb') as f:
            f.write(self._marc_record.as_marc())

    @property
    def identifier(self):
        id_field = self._marc_record['001']
        if not id_field:
            return 'unknown_id'
        id_ = id_field.value()
        m = re.match(r'^IT ICCU (.*)$', id_)
        if m:
            id_ = m.group(1)

        # Sanifica l'ID per evitare caratteri pericolosi nel filename
        id_ = re.sub(r'[^A-Za-z0-9_-]', '_', id_)
        return id_


class RecordsFactory(object):
    def __init__(self, marc_file):
        # Aggiunta gestione UTF-8 e caratteri problematici
        self._reader = pymarc.MARCReader(
            open(marc_file, 'rb'),
            to_unicode=True,
            force_utf8=True,
            utf8_handling='ignore'
        )

    @property
    def records(self):
        for record in self._reader:
            yield Record(record)


class Main(object):
    def __init__(self, marc_file, out_dir):
        self._marc_file = marc_file
        self._out_dir = out_dir

    def __call__(self):
        # Crea la directory di output se non esiste
        os.makedirs(self._out_dir, exist_ok=True)
        factory = RecordsFactory(self._marc_file)

        for rec in factory.records:
            outpath = os.path.join(self._out_dir, rec.identifier + '.mrc')
            rec.write(outpath)
        return 1


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <input_file.mrc> <output_directory>")
        sys.exit(1)
    main = Main(sys.argv[1], sys.argv[2])
    sys.exit(main())
