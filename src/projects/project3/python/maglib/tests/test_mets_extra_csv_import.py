import os
import unittest

from maglib import Metadigit
from maglib.mets_extra_csv_import import (
    MetsExtraImport,
    MetsExtraInfoLoaderSingle,
)

from .test_csv_import import CsvFileBuilder


class MetsExtraImportTC(unittest.TestCase):
    def test_from_empty(self):
        m = Metadigit()
        csv_file = CsvFileBuilder.build(
            (
                "mods:identifier type=subsis",
                'mods:identifier type="cont"',
                "mods:identifier type='cont'",
            ),
            ("id-subsis", "id-cont", "id-cont2"),
        )
        m = Metadigit()
        m.extra.add_instance().mets.add_instance()

        info_loader = MetsExtraInfoLoaderSingle(csv_file)

        MetsExtraImport.do_import(m.extra[0].mets[0], info_loader.info)
        os.remove(csv_file)

        mods = m.extra[0].mets[0].dmdSec[0].mdWrap[0].xmlData[0].mods[0]
        self.assertEqual(len(mods.identifier), 3)
        self.assertEqual(mods.identifier[0].type.value, "subsis")
        self.assertEqual(mods.identifier[0].value, "id-subsis")
        self.assertEqual(mods.identifier[1].type.value, "cont")
        self.assertEqual(mods.identifier[1].value, "id-cont")
        self.assertEqual(mods.identifier[2].type.value, "cont")
        self.assertEqual(mods.identifier[2].value, "id-cont2")
