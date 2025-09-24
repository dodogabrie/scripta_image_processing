# -*- coding: utf-8 -*-

import re

from maglib.unimarc_import.base import UnimarcMapper, FunctionsMap
from maglib.unimarc_import.base_readers import MultiSubFieldsIR, InfoReader, \
    TitleReaderMixin, InfoReadException
from maglib.unimarc_import.readers import \
    Type, BibLevel, Identifier, Date100, Title, Language, Date210d, Format2, \
    BasePublisher, Description300, Contributor702, Contributor712



class PeriodicoMapper(UnimarcMapper):
    type = 'periodico'
    version = '1.8'

    def __init__(self, records_retriever, virtual_bid_tester):
        self._records_retriever = records_retriever
        self._virtual_bid_tester = virtual_bid_tester
        self._function_codes = FunctionsMap()
        super(PeriodicoMapper, self).__init__()

    def _build_readers(self):
        readers = (
            Type(),
            BibLevel(),
            Identifier(),
            DatePeriodico(),
            Language(),
            Title(),
            MultiSubFieldsIR('relation', '200', ('d',),
                             prefix="'titolo parallelo:' "),
            PublisherPeriodico(),
            Format2(),
            MultiSubFieldsIR('relation', '410',
                             ('a', 'v'), "'collana:' ", ' ; '),
            MultiSubFieldsIR('relation', '423', ('a',),
                             prefix="'pubblicato con:' "),
            )

        readers += tuple(
            RelationPeriodico(str(f))
            for f in list(range(430, 438)) + list(range(440, 449)))

        # campi description
        readers += (
            Description326(),
            Description300(),
            MultiSubFieldsIR('description', '207', ('a',),
                             prefix='[numerazione] '),
            # PrefixInfixIR('description', '436', 'a', 'e',
            #               'Formato dall\'unione di ', ' e di '),
            # MSFIRCollapseSpace('description', '437', ('a', 'e'), 'Separato da '),
            # PrefixInfixIR('description', '446', 'a', 'e',
            #               'Scisso in ', ' e '),
            # PrefixInfixIR('description', '447', 'a', 'e',
            #               'Fuso con ', ' per formare '),
            )

        readers += (
            PeriodicoRelation510(),
            Subject606(),
            MultiSubFieldsIR('subject', '676', ('a', 'c', '9'), '', ' - '),
            Contributor702(self._records_retriever, self._function_codes),
            Contributor712(self._records_retriever, self._function_codes),
            )

        return readers


class Date100Periodico(Date100):
    """legge la data dal campo 100 per i periodici"""
    def read(self, marc_record):
        readed = super(Date100Periodico, self).read(marc_record)
        if len(readed) == 2 and readed[1] == '9999':
            return [ readed[0] + '-' ]
        if readed and marc_record['100'].value()[8] == 'a':
            return [ readed[0] + '-' ]
        return readed


class DatePeriodico(InfoReader):
    """legga la data dal campo 100 e 210d"""
    info_name = 'date'
    def __init__(self):
        self._date100_reader = Date100Periodico()
        self._date210d_reader = Date210d()

    def read(self, marc_record):
        readed = self.read_from_210d(marc_record)
        if readed:
            return [readed]
        readed210 = self._date210d_reader.read(marc_record)
        if readed210:
            return readed210
        return self._date100_reader.read(marc_record)


    def read_from_210d(self, marc_record):
        f100 = marc_record['100'].value()
        f210 = marc_record['210']
        if f100[8] == 'f' and (not f100[13:17].strip() or f100[13:17] == '----'):
            if f210 and f210['d'] and re.match(r'\d+-$', f210['d'].strip()):
                return f210['d'].strip()
        return None


class Description326(MultiSubFieldsIR):
    def __init__(self):
        super(Description326, self).__init__('description', '326', ('a', 'b'))

    def read(self, marc_record):
        readed = super(Description326, self).read(marc_record)
        if not readed or readed[0].lower() == 'sconosciuto':
            return []
        return readed


class RelationPeriodico(TitleReaderMixin, MultiSubFieldsIR):
    def __init__(self, field_n):
        MultiSubFieldsIR.__init__(self, 'relation', field_n, ('a', 'e'),
                                  separator= ' ')


class Subject606(MultiSubFieldsIR):
    def __init__(self):
        super(Subject606, self).__init__(
            'subject', '606', ('a', 'j', 'y', 'x', 'z'), '', ' - ')
    def _read_subfield(self, field, subfield_n):
        if subfield_n != 'x':
            return super(Subject606, self)._read_subfield(field, subfield_n)
        values = [self._decode_string(v) for v in field.get_subfields('x')]
        return ' - '.join(values)



class PublisherPeriodico(BasePublisher):
    _local_languages = ('ita', 'lat')

    def __init__(self):
        self._lang_reader_101 = Language('101')
        self._lang_reader_102 = Language('102')
        self._date_reader = DatePeriodico()
        super(PublisherPeriodico, self).__init__()

    def read(self, marc_record):
        f210 = marc_record['210']
        if not f210:
            return []

        acs = self._read_ac_couples(f210)
        first_part = ' ; '.join([' : '.join(filter(None, ac)) for ac in acs])
        if self._use_210d(marc_record):
            first_part = ', '.join(filter(
                    None, (first_part, self._read_210d(marc_record))))
        first_part = self._balance_part1_final_parenthesis(
            marc_record, first_part)            

        egs = self._read_eg_couples(f210, acs)
        second_part = ' ; '.join([' : '.join(filter(None, eg)) for eg in egs])

        value = ' ; '.join(filter(None, (first_part, second_part)))
        if self._use_620d(marc_record):
            value = '%s %s' % (
                value, self._read_620d(marc_record))
            value = value.strip()
        return [self._clean_value(value)]


    def _use_210d(self, marc_record):
        if not super(PublisherPeriodico, self)._use_210d(marc_record):
            return False
        if marc_record['100'].value()[8] == 'b':
            return False
        if self._date_reader.read_from_210d(marc_record):
            return False
        if re.search(r'\d{3,4}-([^\d]|$)', marc_record['210']['d']):
            if marc_record['100'].value()[8] == 'a':
                return False
            if marc_record['100'].value()[8] == 'f':
                return False

            raise InfoReadException(
                '%s: contattare l\'iccu per 210$d' % marc_record['001'].value())
        return True

    def _work_is_in_foreign_lang(self, marc_record):
        readed_lang_101 = self._lang_reader_101.read(marc_record)
        readed_lang_102 = self._lang_reader_102.read(marc_record)
        for lang in readed_lang_101 + readed_lang_102:
            if not lang in self._local_languages:
                return True

    def _use_620d(self, marc_record):
        if not marc_record['620'] or not marc_record['620']['d']:
            return False
        if not self._work_is_in_foreign_lang(marc_record):
            return False

        f620d = self._decode_string(marc_record['620']['d'])
        if marc_record['200']:
            sfs_a = self._read_subfields(marc_record['200'], 'a')
            sfs_e = self._read_subfields(marc_record['200'], 'e')
            if f620d in sfs_a + sfs_e:
                return False
        return True

    def _read_620d(self, marc_record):
        values = []
        for f620 in marc_record.get_fields('620'):
            values.extend(f620.get_subfields('d'))
        return ' ; '.join(values)

# class FormatPeriodico(Format):
#     def __init__(self):
#         MultiSubFieldsIR.__init__(
#             self, 'format', '215', ('c', 'd', 'e'), separator=' ; ')

#     def read(self, marc_record):
#         prefix = ''
#         f215 = marc_record['215']
#         if f215:
#             prefix = self._decode_string(f215['a'])
#         suffix = super(FormatPeriodico, self).read(marc_record)
#         suffix = suffix[0] if suffix else ''


#         components = filter(None, [ prefix, suffix ])
#         if components:
#             return [ self._clean_value(' : '.join(components)) ]
#         return []


class PeriodicoRelation510(MultiSubFieldsIR):
    def __init__(self):
        super(PeriodicoRelation510, self).__init__(
            'relation', '510', ('a',),
            prefix="'titolo parallelo:' ")

    def read(self, marc_record):
        if marc_record['200'] and marc_record['200']['d']:
            return []
        return super(PeriodicoRelation510, self).read(marc_record)

# class PrefixInfixIR(InfoReader):
#     """legge l'informazione da una coppia di sottocampi, inserendo un prefisso
#     al primo sottocampo e un infisso fra i due"""
#     def __init__(self, info_name, field_n,
#                  subfield_a, subfield_b, prefix, infix):
#         super(PrefixInfixIR, self).__init__(info_name,)
#         self._field_n = field_n
#         self._subfield_a = subfield_a
#         self._subfield_b = subfield_b
#         self._prefix = prefix
#         self._infix = infix

#     def read(self, marc_record):
#         field = marc_record[self._field_n]
#         if not (field and field[self._subfield_a] and field[self._subfield_b]):
#             return []
#         return '%s%s%s%s' % (
#             self._prefix, self._clean_string(field[self._subfield_a]),
#             self._infix, self._clean_string(field[self._subfield_b]))
