# -*- coding: utf-8 -*-

import os
import re
import logging

from pymarc import MARCReader

from maglib.script.common import BibAdder, MagOperationError


log = logging.getLogger('maglib.unimarc_importer')

class UnimarcMapper(object):
    """legge le informazioni peri il mag da un record unimarc
    e presenta quelle importabili in un mag come chiavi di dizionario.
    Per ogni chiave c'è una lista di valori importati"""
    def __init__(self, info_readers=()):
        """:info_readers: lista di InfoReader"""
        self._readers = list(info_readers)
        self._readers.extend(self._build_readers())

        self._info_names = [ reader.info_name for reader in self._readers ]

    @property
    def info_names(self):
        """i nomi delle informazioni dublin core possibilmente leggibili"""
        return self._info_names

    def read(self, marc_record):
        """legge le informazioni dal record e le ritorna in un dizionario
        :marc_record: pymarc.record.Record da cui leggere le informazioni"""
        info_dict = self._init_info_dict()
        for reader in self._readers:
            info_values = [ self._global_info_fix(v)
                            for v in reader.read(marc_record) ]
            info_dict[reader.info_name].extend(info_values)
        return info_dict

    def _build_readers(self):
        return ()

    def _init_info_dict(self):
        # inizializza il dizionario con le informazioni disponibili
        return dict( [(info, []) for info in self.info_names] )

    def _global_info_fix(self, v):
        return v


class UnimarcBibAdder(BibAdder):
    """importa le informazioni da un record unimarc nel nodo bib del mag"""
    def __init__(self, bid, unimarc_path):
        """:bid: bid dell'oggetto che il mag descrive
        :unimarc_path: path che contiene il record unimarc ed eventualmente
        quelli collegati"""
        self._bid = bid
        self._records_retriever = DirRecordsRetriever(unimarc_path)

    def _build_bib_info(self):
        mapper = self._build_mapper()
        record = self._records_retriever.get_record(self._bid)
        if not record:
            raise MagOperationError(
                'can\'t find unimarc record for bid %s' % self._bid)
        return mapper.read(record)

    def _build_mapper(self):
        raise NotImplementedError()


class RecordsRetriever(object):
    """ottiene un record unimarc per un bid"""
    def get_record(self, bid):
        raise NotImplementedError()

class VoidRecordsRetriever(RecordsRetriever):
    def get_record(self, bid):
        return None


class DirRecordsRetriever(RecordsRetriever):
    """ottiene i record da file nominati bid.mrc contenuti ricorsivamente in una
    cartella che contengono il record di bid come primo record"""
    def __init__(self, dIr):
        self._dIr = dIr

    def get_record(self, bid):
        bid = Bid.from_prefixed_bid(bid).value
        for root, dirs, files in os.walk(self._dIr):
            for f in files:
                if f == ('%s.mrc' % bid):
                    reader = MARCReader(open(os.path.join(root, f), 'rb'))
                    for record in reader:
                        break
                    return record
        return None


class VirtualBidTester(object):
    """sa quali bid sono virtuali e quali no"""
    def __call__(self, bid):
        raise NotImplementedError()


class StubVirtualBidTester(VirtualBidTester):
    def __call__(self, bid):
        return True


class Bid(object):
    def __init__(self, value):
        self._value = value

    @classmethod
    def from_prefixed_bid(cls, prefixed_bid):
        bid = re.sub(r'^IT\\ICCU\\', '', prefixed_bid)
        bid = bid.replace('\\', '')
        return cls(bid)

    @classmethod
    def from_blank_prefixed_bid(cls, blank_prefixed_bid):
        bid = re.sub(r'IT ICCU ', '', blank_prefixed_bid)
        bid = bid.replace(' ', '')
        return cls(bid)

    @property
    def value(self):
        return self._value


class CodeMap(object):
    file_name = None
    _map = None

    def __init__(self):
        if self._map is None:
            self._build_map()

    def __getitem__(self, key):
        return self._map[key]

    def get(self, key, default=None):
        return self._map.get(key, default)

    @classmethod
    def _build_map(cls):
        cls._map = {}
        table_file = os.path.join(
            os.path.dirname(__file__), 'code_tables', cls.file_name)
        for line in open(table_file, 'rt'):
            space_index = line.find(' ')
            key = line[:space_index]
            value = line[space_index + 1:].strip()
            if not value:
                value = None
            cls._map[key] = value


class FunctionsMap(CodeMap):
    """tabella LETA dei codici unimarc
    cfr http://www.iccu.sbn.it/opencms/export/sites/iccu\
    /documenti/2011/TB_CODICI.pdf"""
    file_name = 'functions'


class MusicalInstrumentsMap(CodeMap):
    """tabella ORGA dei codici unimarc
    cfr http://www.iccu.sbn.it/opencms/export/sites/iccu\
    /documenti/2011/TB_CODICI.pdf"""
    file_name = 'musical_instruments'
