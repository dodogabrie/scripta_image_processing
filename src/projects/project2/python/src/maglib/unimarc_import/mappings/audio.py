# -*- coding: utf-8 -*-

import re

from maglib.unimarc_import.base import UnimarcMapper, FunctionsMap
from maglib.unimarc_import.base_readers import \
    InfoReader, ParentRelationIRMixin, ParentFallbackIRMixin, TitleReaderMixin

from maglib.unimarc_import.readers import \
    Type, BibLevel, Identifier, Date100, Language, Date210d, Format, Title,\
    Description300, MultiSubFieldsIR, MultiSubFieldsFallbackIR, BasePublisher, \
    RelationIR, RelationParentTitleIR, Relation423, Relation463, \
    Creator700_701, Contributor702, Contributor712, Creator710_711


class AnticoMapper(UnimarcMapper):
    type = 'risorsa sonora di musica'
    version = '1.9'

    def __init__(self, records_retriever, virtual_bid_tester):
        self._records_retriever = records_retriever
        self._virtual_bid_tester = virtual_bid_tester
        self._function_codes = FunctionsMap()
        super(AnticoMapper, self).__init__()

    def _build_readers(self):
        return (
            Type(),
            BibLevel(),
            Identifier(),

            Date100(),
            Language(),
            TitleAntico(),
            PublisherAntico(self._records_retriever),
            Date210d(),
            Format(),

            #Description317(),
            MultiSubFieldsIR('description', '303', ('a',), prefix="'dedica:' "),
            #SSFIRCollapseSpace('description', '012', 'a', "'impronta:' "),
            Marca(),
            Description300Antico(),

            MiscTitleReader('relation', '410', ('a', 'v'),
                            "'collana:' ", ' ; '),
            Relation423(self._virtual_bid_tester),
            RelationParentTitleIR('461', "'fa parte di:' ", self._virtual_bid_tester),
            RelationParentTitleIR('462', "'fa parte di:' ", self._virtual_bid_tester),
            Relation463(self._virtual_bid_tester),
            RelationIR('464', "'fa parte di:' ",
                       self._virtual_bid_tester, repeat=True),
            MultiSubFieldsIR('relation', '488', ('a',), repeat=True),
            MiscTitleReader('relation', '500', ('a',),
                             prefix="'titolo uniforme:' ", repeat=True),
            MiscTitleReader('relation', '510', ('a',),
                             prefix="'titolo parallelo:' '", repeat=True),
            MiscTitleReader('relation', '517', ('a',),
                             prefix="'variante del titolo:' ", repeat=True),

            Creator700_701(self._records_retriever, '700'),
            Creator700_701(self._records_retriever, '701'),
            Contributor702(self._records_retriever, self._function_codes),
            Creator710_711(self._records_retriever, '710'),
            Creator710_711(self._records_retriever, '711'),
            Contributor712(self._records_retriever, self._function_codes),
            )


class TitleAntico(ParentRelationIRMixin, Title):
    def read(self, marc_record):
        title_field = marc_record['200']
        if not title_field:
            return []
        if self._work_is_part(marc_record):
            relation_field = self._first_relation_field(marc_record)
            return [ self._clean_value('%s. %s' % (
                    self._decode_string(relation_field['a']),
                    self._decode_string(title_field['a'])))
                     ]
        return Title.read(self, marc_record)

class MiscTitleReader(TitleReaderMixin, MultiSubFieldsIR):
    pass

class Description300Antico(Description300):
    def _filter_value(self, value):
        for regex in (
            r'^\s*Segn.:', r'^\s*Marca', r'^\s*Colophon', r'^.*\[ast\]'):
            if re.match(regex, value):
                return False
        return True

class Marca(InfoReader):
    """legge la marca da 306$a, o in sua mancanza da 921$b"""
    info_name = 'description'
    def __init__(self):
        self._reader_306a = MultiSubFieldsIR(
            'description', '306', 'a', prefix="'marca:' ")
        self._reader_921b = MultiSubFieldsIR(
            'description', '921', 'b', prefix="'marca:' ")

    def read(self, marc_record):
        readed = self._reader_306a.read(marc_record)
        if not readed:
            readed = self._reader_921b.read(marc_record)
        readed = filter(self._filter_value, readed)
        return readed

    def _filter_value(self, v):
        return not v.lower() in (
            'marca non censita',
            'marca non controllata')



class PublisherAntico(ParentFallbackIRMixin, TitleReaderMixin, BasePublisher):
    def __init__(self, records_retriever):
        ParentFallbackIRMixin.__init__(self, records_retriever)
        BasePublisher.__init__(self)

    def _read_not_fallback(self, marc_record):
        sf_a, sf_c, sf_e, sf_g = self._read_subfields_aceg(marc_record['210'])

        part1a = ' : '.join(filter(None, (sf_a, sf_c)))
        part1b = ' : '.join(filter(None, (sf_e, sf_g)))
        part1 = ' ; '.join(filter(None, (part1a, part1b)))
        if not part1: # se non c'è 210, si legge il publisher dalla scheda del genitore
            return []
        part1 = self._balance_part1_final_parenthesis(marc_record, part1)

        part2a = self._read_620d(marc_record)
        part2b = self._read_712a(marc_record)
        part2 = ' ; '.join(filter(None, (part2a, part2b)))
        part2 = ('[%s]' % part2) if part2 else ''

        if self._use_210d(marc_record):
            part3 = self._read_210d(marc_record)
        else:
            part3 = ''

        value = ' '.join(filter(None, (part1, part2)))
        value = ', '.join(filter(None, (value, part3)))
        if value:
            return [self._clean_value(value)]
        return []

    def _read_620d(self, marc_record):
        values = []
        sfs_a = self._read_subfields(marc_record['210'], 'a')
        sfs_e = self._read_subfields(marc_record['210'], 'e')
        #sfs_620d = self._read_subfields(marc_record['620'], 'd')

        for f620 in marc_record.get_fields('620'):
            sfs = self._read_subfields(f620, 'd')
            for sf in sfs:
                if not sf in sfs_a + sfs_e + values:
                    values.append(sf)
        return ' ; '.join(values) if values else None

    def _read_712a(self, marc_record):
        values = []
        sfs_c = self._read_subfields(marc_record['210'], 'c')
        sfs_g = self._read_subfields(marc_record['210'], 'g')
        for f in marc_record.get_fields('712'):
            if f['4'] in ('610', '650'):
                v = self._decode_string(f['a']).strip()
                if not v in sfs_c + sfs_g + values:
                    values.append(v)
        if values:
            return TitleReaderMixin._clean_value(' ; '.join(values))
        return None


# class TitleAntico(ParentRelationIRMixin, InfoReader):
#     info_name = 'title'
#     def __init__(self):
#         self._simple_title_reader = Title()

#     def read(self, marc_record):
#         title_field = marc_record['200']
#         if not title_field or not title_field['a']:
#             return []

#         if self._work_is_part(marc_record):
#             relation_field = self._first_relation_field(marc_record)
#             return [ self._clean_value('%s. %s' % (
#                     self._decode_string(relation_field['a']),
#                     self._decode_string(title_field['a'])))
#                      ]
#         return self._simple_title_reader.read(marc_record)

#     def _clean_value(self, v):
#         return re.sub(r'[\x88\x89\x98\x9c]', '', v)

