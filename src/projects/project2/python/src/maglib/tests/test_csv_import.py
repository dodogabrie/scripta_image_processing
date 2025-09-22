"""test for maglib.csv_import"""

import csv
import os
import tempfile
from unittest import TestCase

from maglib import Metadigit
from maglib.csv_import import CsvBibInfoCreatorSingle
from maglib.script.common import BibImport


class CsvFileBuilder:
    @classmethod
    def build(self, *rows):
        tmpfd, tmppath = tempfile.mkstemp(suffix=".csv")
        tmpf = os.fdopen(tmpfd, "w")
        csv_writer = csv.writer(tmpf)
        csv_writer.writerows(rows)
        tmpf.close()
        return tmppath


class SingleImportTC(TestCase):
    def test_from_empty(self):
        m = Metadigit()
        csv_file = CsvFileBuilder.build(
            ("title", "<dc:creator>", "creator", "stpiece_per", "year", "issue"),
            ("tit", u"creàt", "creat2", "(1992:02)", "1992", "n.123"),
        )

        bib_info_creator = CsvBibInfoCreatorSingle(csv_file)
        bib_info = bib_info_creator.bib_info
        BibImport.do_import(m.bib.add_instance(), bib_info)

        self.assertEqual(len(m.bib), 1)
        b = m.bib[0]
        self.assertEqual(len(b.title), 1)
        self.assertEqual(b.title[0].value, "tit")
        self.assertEqual(len(b.creator), 2)
        self.assertEqual(b.creator[0].value, u"creàt")
        self.assertEqual(b.creator[1].value, u"creat2")
        self.assertEqual(len(b.piece), 1)
        p = b.piece[0]
        self.assertEqual(p.stpiece_per.get_value(), "(1992:02)")
        self.assertEqual(p.year.get_value(), "1992")
        self.assertEqual(p.issue.get_value(), "n.123")

        os.remove(csv_file)
