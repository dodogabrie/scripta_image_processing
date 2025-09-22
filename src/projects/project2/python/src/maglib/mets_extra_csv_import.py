import logging
import re

from maglib import Metadigit
from maglib.csv_import import MagInfoCsvReader
from maglib.mag.mets_elements import MODS_IDENTIFIER_TYPES, Mets
from maglib.utils.misc import ensure_mag_elements

log = logging.getLogger(__name__)


class MetsExtraImport:
    @classmethod
    def do_import(cls, mets: Mets, info: dict):
        for info_name, info_values in info.items():
            if info_name.startswith("mods-identifier:"):
                mods_id_type = info_name[len("mods-identifier:") :]
                cls._import_mods_identifier(mets, mods_id_type, info_values)

    @classmethod
    def _import_mods_identifier(cls, mets: Mets, mods_id_type: str, values):
        ensure_mag_elements(mets, "dmdSec.mdWrap.xmlData.mods")

        mods_identifier = mets.dmdSec[0].mdWrap[0].xmlData[0].mods[0].identifier

        for value in values:
            mods_identifier.add_instance().value = value
            mods_identifier[-1].type.value = mods_id_type


class MetsExtraInfo(dict):
    keys = [f"mods-identifier:{typ}" for typ in MODS_IDENTIFIER_TYPES]

    def __setitem__(self, key, value):
        if key not in self.keys:
            raise ValueError(f"key {key} unknown for bib info")
        return super().__setitem__(key, value)

    def add_value(self, key, value):
        if key not in self:
            self[key] = []
        self[key].append(value)


class MetsExtraCsvReader(MagInfoCsvReader):
    def _normalize_fieldname(self, fieldname: str):
        f = fieldname.strip().lower()
        for typ in MODS_IDENTIFIER_TYPES:
            regex = f"identifier type=[\"']?{typ}[\"']?"
            if re.search(regex, f):
                return f"mods-identifier:{typ}"
        log.warning("unrecognized header %s", fieldname)
        return f


class MetsExtraCsvImportError(Exception):
    pass


class MetsExtraInfoLoaderSingle:
    """Loads mets extra info to import from a csv

    Needs a csv with an header row and a single data row,
    see CsvBibInfoCreatorSingle

    """

    def __init__(self, csv_file: str, encoding="utf-8"):
        self._encoding = encoding
        with open(csv_file, "r", encoding=encoding) as csv_fp:
            self._info = self._read(csv_fp)

    @property
    def info(self) -> dict:
        return self._info

    def _read(self, csv_fp):
        try:
            csv_reader = MetsExtraCsvReader(csv_fp)
        except IOError as exc:
            raise MetsExtraCsvImportError(exc)
        rows = list(csv_reader)
        if len(rows) != 1:
            raise MetsExtraCsvImportError(
                "please use csv with one data row for single-mag import"
            )

        return self._build_info_from_row(rows[0])

    def _build_info_from_row(self, row):
        info = MetsExtraInfo()
        for key, values in row.items():
            if key not in info.keys:
                log.warning("ignoring unknown field %s" % key)
                continue
            for value in values:
                value = value.strip()
                if value:
                    info.add_value(key, value)
        return info


if __name__ == "__main__":
    import sys

    info_creator = MetsExtraInfoLoaderSingle(sys.argv[1])
    m = Metadigit()
    m.extra.add_instance()
    m.extra[0].mets.add_instance()
    MetsExtraImport.do_import(m.extra[0].mets[0], info_creator.info)

    print(m.to_string())
