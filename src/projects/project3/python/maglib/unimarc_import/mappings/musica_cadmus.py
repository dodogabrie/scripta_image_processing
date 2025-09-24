# -*- coding: utf-8 -*-

import re


from maglib.unimarc_import.base import UnimarcMapper, FunctionsMap,\
    VoidRecordsRetriever
from maglib.unimarc_import.base_readers import InfoReader, TitleReaderMixin
from maglib.unimarc_import.readers import *
from maglib.unimarc_import.mappings.manoscritto_musicale import MusicalTonesMap




class MusicaCadmusMapper(UnimarcMapper):
    # scritto per torino dicembre 2013
    type = 'musica cadmus'
    version = '1.0'
    identifier = 'mapping_Unimarc_musica_CADMUS_MAG'
    function_codes = FunctionsMap()

    def _build_readers(self):
        return (
            Type(),
            BibLevel(),
            IdentifierCadmus(),
            Date100(),
            Language(),
            Description1(),
            Description316(),
            TitleFull(),
            Format(),
            Publisher(),
            Relation(),
            Relation517(),
            Creator(),
            ContributorCadmus(VoidRecordsRetriever(), self.function_codes),
            Incipit(),
        )


class Description1(InfoReader):
    info_name = 'description'
    def read(self, marc_record):
        parts = (
            self._read128(marc_record),
            self._read208(marc_record),
            self._read300(marc_record),
            self._read327(marc_record),
            self._read321(marc_record)
        )
        parts = filter(None, parts)
        return [ ' ; '.join(parts) ]


    def _read128(self, marc_record):
        f128 = marc_record['128']
        if not f128:
            return ''
        components = []
        for sfa in f128.get_subfields('a'):
            components.append(self._clean_value(sfa))
        components = filter(None, components)
        return ', '.join(components)

    def _read208(self, marc_record):
        if not marc_record['208']:
            return ''
        if not marc_record['208']['a']:
            return ''
        return self._clean_value(marc_record['208']['a'])

    def _read300(self, marc_record):
        components = []
        for f in marc_record.get_fields('300'):
            if not f['a']:
                continue
            components.append(self._clean_value(f['a']))
        components = filter(None, components)
        components = map(self._remove_sentences_stop, components)
        return ' ; '.join(components)

    def _read327(self, marc_record):
        if not marc_record['327']:
            return ''
        if not marc_record['327']['a']:
            return ''
        return self._clean_value(marc_record['327']['a'])

    def _read321(self, marc_record):
        components = []
        f321 = marc_record['321']
        if not f321:
            return ''
        if f321['a']:
            components.append(self._clean_value(f321['a']))
        if f321['b']:
            components.append(self._clean_value(f321['b']))
        if f321['c']:
            components.append(self._clean_value(f321['c']))
        components = filter(None, components)
        return ', '.join(components)

    def _remove_sentences_stop(self, value):
        return re.sub(r'\.(?!\s*\w)', '', value)


class Description316(InfoReader):
    info_name = 'description'
    def read(self, marc_record):
        parts = []
        for f in marc_record.get_fields('316'):
            sfa = f['a']
            if sfa:
                sfa = self._decode_string(sfa).strip()
                if sfa:
                    parts.append(sfa)
        if parts:
            return [ self._clean_value(' ; '.join(parts)) ]
        return []

    def _clean_value(self, value):
        v = super(Description316, self)._clean_value(value)
        return re.sub(r'\.(?!\s*\w)', '', v)


class IdentifierCadmus(InfoReader):
    info_name = 'identifier'
    def read(self, marc_record):
        return [ 'cadmus_%s' % self._decode_string(
            marc_record['001'].value()) ]


class Format(InfoReader):
    info_name = 'format'
    def _read_sf(self, marc_record, field_n, subfield_n):
        if not marc_record[field_n]:
            return ''
        return marc_record[field_n][subfield_n] or ''

    def read(self, marc_record):
        part1 = self._read_sf(marc_record, '208', 'a')
        part2 = self._read_sf(marc_record, '215', 'a')
        part3 = self._read_sf(marc_record, '215', 'd')

        first = ', '.join(filter(None, (part1, part2)))
        value = ' ; '.join(filter(None, (first, part3)))
        value = re.sub(',(?! )', ', ', value)
        value = re.sub('  +', ' ', value)
        return [value]
        


class Publisher(InfoReader):
    info_name = 'publisher'
    def read(self, marc_record):
        part210a = self._read210a(marc_record)
        part620a = self._read620a(part210a, marc_record)
        part210c = self._read210c(marc_record)

        if part620a or part210c:
            second_part = ' ; '.join(filter(None, (part620a, part210c)))
            second_part = '[%s]' % second_part
        else:
            second_part = ''

        if part210a or second_part:
            return [ ' '.join((part210a, second_part)).strip() ]
        return [ ]


    def _read210a(self, marc_record):
        parts = []
        if marc_record['210']:
            for sf in marc_record['210'].get_subfields('a'):
                if self._clean_value(sf):
                    parts.append(self._clean_value(sf))
        if not parts and marc_record.leader[6] == 'd':
            return 's.l. : copia'
        return '; '.join(parts)

    def _read620a(self, part210a, marc_record):
        for s in ('Paris', 'Wien', 'Vienne', 'In Venetia', 'Leipzig',
                  'Spire', 'Munic', '[Paris]', 'Parsi', 'Berlin', 'Dublin',
                  'Mannheim et Munich', u'À Paris', 'Mayland', 'Milan', 'Venetia',
                  'Turin', 'Mediolani'):
            if part210a.find(s) > -1:
                if marc_record['620'] and marc_record['620']['a']:
                    return self._clean_value(marc_record['620']['a'])
        return ''
        # if re.search('\bMilan\b', part210a):
        #     if marc_record['620'] and marc_record['620']['a']:
        #         return self._clean_value(marc_record['620']['a'])
        # return ''

    def _read210c(self, marc_record):
        parts = []
        if not marc_record['210']:
            return
        for sf in marc_record['210'].get_subfields('c'):
            sf = self._clean_value(sf)
            if re.match(r'^\d{4}$', sf):
                continue
            parts.append(sf)
        return '; '.join(parts)

    def _clean_value(self, v):
        v = super(Publisher, self)._clean_value(v)
        return v.replace('*', '')



class Relation(TitleReaderMixin, InfoReader):
    info_name = 'relation'
    def read(self, marc_record):
        prefix = self._clean_value(self._read_sf(marc_record, '500', 'a'))
        if prefix:
            prefix += ': '
        parts = []
        parts.append(
            self._clean_value(
                self._read_sf(marc_record, '500', 'i')).replace('*', ''))
        parts.append(self._read936i(marc_record))
        parts.append(
            self._clean_value(self._read_sf(marc_record, '945', 'c')))
        parts[-1] = re.sub(r',(?!\s)', ', ',  parts[-1])
        parts.append(self._read500s(marc_record))

        musical_tones_map = MusicalTonesMap()
        parts.append(
            musical_tones_map.get(
                self._clean_value(self._read_sf(marc_record, '936', 'g'))))
        parts.append(
            self._clean_value(self._read_sf(marc_record, '500', 'n')))
        parts = filter(None, parts)

        if prefix or parts:
            return [ '\'titolo uniforme:\' %s%s' % (prefix, '. '.join(parts)) ]


    def _read936i(self, marc_record):
        if not marc_record['936']:
            return ''
        parts = []
        for sf in marc_record['936'].get_subfields('i'):
            sf = self._clean_value(sf)
            if sf:
                parts.append(sf)
        return ', '.join(parts)

    def _read500s(self, marc_record):
        if not marc_record['500']:
            return ''
        for sf in marc_record['500'].get_subfields('s'):
            v = self._clean_value(sf)
            if not v.startswith('n'):
                return 'op n. %s' % v
        return ''
        # v = self._clean_value(marc_record['500']['s'])
        # if v.startswith('n'):
        #     return ''
        # return 'op n. %s' % v

    def _read_sf(self, marc_record, field_n, subfield_n):
        if not marc_record[field_n]:
            return ''
        return marc_record[field_n][subfield_n] or ''

    def _clean_value(self, v):
        v = super(Relation, self)._clean_value(v)
        v = re.sub(r',(?!\s)', ', ', v)
        return v


class Relation517(MultiSubFieldsIR):
    def __init__(self):
        super(Relation517, self).__init__(
            'relation', '517', 'a', repeat=True)

    def _clean_value(self, v):
        v = super(Relation517, self)._clean_value(v)
        return v.replace('*', '')


class Creator(Creator700_701):
    def __init__(self):
        super(Creator, self).__init__(None, '700')

    def read(self, marc_record):
        return super(Creator, self)._read_not_fallback(marc_record)

    def _clean_value(self, v):
        v = super(Creator, self)._clean_value(v)
        return v.replace('*', '-')


class ContributorCadmus(Contributor702New):
    def _clean_value(self, value):
        v = super(ContributorCadmus, self)._clean_value(value)
        return v.replace('*', '-')

    def _filter_sf4(self, sf4_value):
        return not sf4_value in ('750', '570')

class Incipit(MultiSubFieldsIR):
    def __init__(self):
        super(Incipit, self).__init__(
            'relation', '936', ('t',), "'incipit:' ", repeat=True)

