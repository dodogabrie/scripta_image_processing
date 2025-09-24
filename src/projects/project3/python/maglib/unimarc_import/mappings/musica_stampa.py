# -*- coding: utf-8 -*-

import re

from maglib.unimarc_import.base import UnimarcMapper, FunctionsMap,\
    MusicalInstrumentsMap
from maglib.unimarc_import.readers import *
from maglib.unimarc_import.base_readers import TitleReaderMixin
from maglib.unimarc_import.base import VoidRecordsRetriever

from maglib.unimarc_import.mappings.manoscritto_musicale import \
    MusicalFormMap, MusicalTonesMap



class MusicaStampaMapper(UnimarcMapper):
    # scritto per torino dicembre 2013
    type = 'musica a stampa'
    version = '1.0'
    identifier = 'mapping_Unimarc_musica_a_stampa_MAG'

    def __init__(self):
        self._functions_map = FunctionsMap()
        self._musical_form_map = MusicalFormMap()
        self._musical_tones_map = MusicalTonesMap()
        self._musical_instruments_map = MusicalInstrumentsMap()
        super(MusicaStampaMapper, self).__init__()


    def _build_readers(self):
        return (
            MusicaStampaType(),
            BibLevel(),
            Identifier(),
            Date100(),
            Language(),
            TitleFull(),
            Publisher(),
            Format2(),
            Description300(),
            # Description316 letto da un altro record unimarc
            Description3(self._musical_instruments_map),

            RelationCollana(),
            # MultiSubFieldsIR('relation', '410',
            #                  ('a', 'v'), "'collana:' ", ' ; '),
            Relation500(self._musical_form_map, self._musical_tones_map,
                        self._musical_instruments_map),
            # MultiSubFieldsIR('relation', '510', ('a',),
            #                  prefix="'titolo parallelo:' ", repeat=True),
            Relation510(),
            Relation517(),
            MultiSubFieldsIR('creator', '700', ('a', 'b', 'c', 'f'),
                             repeat=True),
            MultiSubFieldsIR('creator', '701', ('a', 'b', 'c', 'f'),
                             repeat=True),
            Contributor702(VoidRecordsRetriever(), self._functions_map),
            Contributor712(VoidRecordsRetriever(), self._functions_map),

        )


class MusicaStampaType(Type):
    def read(self, marc_record):
        # type dovrebbe essere sempre fisso
        readed = super(MusicaStampaType, self).read(marc_record)
        assert readed == ['musica a stampa']
        return readed


class Publisher(BasePublisher):
    def read(self, marc_record):
        f210 = marc_record['210']
        if not f210:
            return []

        sf_a, sf_c, sf_e, sf_g = self._read_subfields_aceg(f210)

        first_part = ' : '.join((filter(None, (sf_a, sf_c))))
        if self._use_210d(marc_record):
            first_part = ', '.join(filter(
                    None, (first_part, self._read_210d(marc_record))))
        first_part = self._balance_part1_final_parenthesis(
            marc_record, first_part)

        second_part = ' : '.join((filter(None, (sf_e, sf_g))))

        value = ' ; '.join(filter(None, (first_part, second_part)))

        part_620d = self._read_620d(marc_record)
        if part_620d:
            value = '%s [%s]' % (value, part_620d)

        return [ self._clean_value(value) ]

    def _read_620d(self, marc_record):
        f620 = marc_record['620']
        if not f620:
            return None

        f210 = marc_record['210']
        if not f210:
            sf_a, sf_c, sf_e, sf_g = [], [], [], []
        else:
            sf_a, sf_c, sf_e, sf_g = self._read_subfields_aceg(f210)

        values = []
        for sf620d in f620.get_subfields('620'):
            v = self._decode_string(sf620d)
            if not v in sf_a + sf_e:
                values.append(v)
        return ' ; '.join(values)


class Relation500(TitleReaderMixin, InfoReader):
    info_name = 'relation'
    def __init__(self, musical_form_map, musical_tones_map,
                 musical_instruments_map):
        self._musical_form_map = musical_form_map
        self._musical_tones_map = musical_tones_map
        self._musical_instruments_map = musical_instruments_map


    def read(self, marc_record):
        readed = []
        for field500 in marc_record.get_fields('500'):
            parts = []
            field928 = self._get_field928(marc_record, field500)
            field929 = self._get_field929(marc_record, field500)
            parts.append(self._read_sf(field500, 'a'))


            parts.append(self._read_928a(field928))
            parts.append(self._read_928c(field928))

            _929b = self._read_sf(field929, 'b')
            if _929b:
                parts.append('op. %s' % _929b)

            parts.append(self._read_sf(field929, 'a'))
            parts.append(self._read_sf(field929, 'f'))

            _929e = self._read_sf(field929, 'e')
            if _929e:
                parts.append(self._musical_tones_map.get(_929e))

            parts.append(self._read_sf(field929, 'c'))
            parts.append(self._read_sf(field929, 'i'))
            parts.append(self._read_sf(field929, 'd'))

            readed.append(u"'titolo uniforme:' " +
                          '. '.join(filter(None, parts)))

        readed = [self._clean_value(r) for r in readed]
        return readed


    def _read_sf(self, field, subfield_n):
        if not field:
            return None
        v = field[subfield_n]
        if v:
            v = self._clean_value(v)
        return v

    def _read_928a(self, field):
        parts = []
        for sf in field.get_subfields('a'):
            v = self._decode_string(sf).strip()
            parts.append(self._musical_form_map.get(v))
        parts = filter(None, parts)
        if parts:
            return ', '.join(parts)
        return None


    def _convert_928c_value(self, v):
        m = re.match(r'^(\d+)(.*)$', v)
        pren = postn = None
        if m:
            pren = m.group(1)
            v = m.group(2).strip()
        m = re.match(r'^(.*?)(\d+)$', v)
        if m:
            v = m.group(1).strip()
            postn = m.group(2)

        #v = self._musical_instruments_map.get(v, v)
        if v:
            v = v.lower()

        if pren:
            v = '%s %s' % (pren, v)
        elif postn:
            v = '%s %s' % (v, postn)
        return v

    def _read_928c(self, field):
        if not field['c']:
            return None
        s = self._decode_string(field['c'])
        values = s.split(',')
        values = [ self._convert_928c_value(v) for v in values ]
        return ', '.join(values)


    def _get_field928(self, marc_record, field500):
        bid = field500['3']
        for f in marc_record.get_fields('928'):
            if f['z'] == bid:
                return f
        return None

    def _get_field929(self, marc_record, field500):
        bid = field500['3']
        for f in marc_record.get_fields('929'):
            if f['z'] == bid:
                return f
        return None

    def _clean_value(self, v):
        v = super(Relation500, self)._clean_value(v)
        v = re.sub(',(?!\s)', ', ', v)
        return v


class RelationCollana(MultiSubFieldsIR):
    def __init__(self):
        MultiSubFieldsIR.__init__(self, 'relation', '410', ())

    def _read_field(self, field):
        sfa = self._read_subfield(field, 'a')
        if not sfa:
            return
        value = sfa
        sff = self._read_subfield(field, 'f')
        if sff:
            value += (' / %s' % sff)
        sfv = self._read_subfield(field, 'v')
        if sfv:
            value += (' ; %s' % sfv)
        return "'collana:' %s" % value



class Relation510(TitleReaderMixin, MultiSubFieldsIR):
    def __init__(self):
        MultiSubFieldsIR.__init__(
            self, 'relation', '510', ('a',),
            prefix="'titolo parallelo:' ", repeat=True)


class Relation517(TitleReaderMixin, MultiSubFieldsIR):
    def __init__(self):
        super(Relation517, self).__init__('relation', '517', ('a',),
                                          repeat=True)
    def _read_field(self, field):
        if field['e'] == 'I':
            self._prefix = "'incipit:' "
        elif field['e'] == 'T':
            self._prefix = "'titolo alternativo:' "
        else:
            pass
            #raise Exception('unexpected value of 517$e: %s' % field['e'])
        return super(Relation517, self)._read_field(field)


class Contributor702(Contributor702New):
    def _read_part2(self, field):
        return super(Contributor702, self)._read_part2(field, ('c', 'f'))

    def _filter_field(self, field):
        sf4 = self._read_subfield(field, '4')
        if sf4 in ('610', '650', '750'):
            return False
        return True

    def _read_part3(self, field):
        sf4 = self._read_subfield(field, '4')
        if sf4 == '570':
            return None
        return super(Contributor702, self)._read_part3(field)


class Contributor712(Contributor712New):
    def _read_part2(self, field):
        return super(Contributor712, self)._read_part2(field, ('c', 'f'))

    def _filter_field(self, field):
        sf4 = self._read_subfield(field, '4')
        if sf4 in ('610', '650', '750'):
            return False
        return True


# class Contributor702(MultiSubFieldsIR, FunctionCodesMixin):
#     def __init__(self, function_codes):
#         FunctionCodesMixin.__init__(self, function_codes)
#         super(Contributor702, self).__init__(
#             'contributor', '702', ('a', 'b', 'c', 'f', '4'))

#     def _read_subfield(self, field, subfield_n):
#         if subfield_n == '4':
#             if not field['4'] or field['4'] == '570':
#                 return None
#             qual = self._convert_function_code(field['4'])
#             if not qual.startswith('<'):
#                 return ', <%s>' % qual
#             return ', %s' % qual
#         return super(Contributor702, self)._read_subfield(field, subfield_n)


# class Contributor712(Contributor702_712):
#     def __init__(self, function_codes):
#         FunctionCodesMixin.__init__(self, function_codes)
#         super(Contributor712, self).__init__(
#             'contributor', '702', ('a', 'c', 'f', '4'))

#     def _read_subfield(self, field, subfield_n):
#         if subfieldn == '4':
#             pass

#     def _read_field(self, field):
#         if field['4'] in ('610', '650'):
#             return None
#         return super(Contributor712, self)._read_field(field)

#     def _read_subfield(self, field, subfield_n):
#         if subfield_n == '4':
#             if not field['4']:
#                 return None
#             qual = self._convert_function_code(field['4'])
#             if not qual.startswith('<'):
#                 return ', <%s>' % qual
#             return ', %s' % qual
#         return super(Contributor712, self)._read_subfield(field, subfield_n)


class Description3(MultiSubFieldsIR):
    info_name = 'description'
    def __init__(self, musical_instruments_map):
        super(Description3, self).__init__(
            'description', '927', ('a', 'c', 'b'), separator=', ', repeat=True)
        self._instruments_map = musical_instruments_map

    def read(self, marc_record):
        readed = super(Description3, self).read(marc_record)
        # collassa i valori dei campi in uno e aggiunge un singolo prefisso
        if readed:
            readed = [ '%s%s' % (
                'Personaggi e interpreti: ', ' ; '.join(readed)) ]
        return readed

    def _read_subfield(self, field, subfield_n):
        readed = super(Description3, self)._read_subfield(field, subfield_n)
        if subfield_n == 'b':
            readed = self._instruments_map.get(readed)
            if readed:
                readed = readed.lower()
        return readed

    def _clean_value(self, v):
        v = super(Description3, self)._clean_value(v)
        return re.sub(r' ?<.*?>', '', v).strip()
