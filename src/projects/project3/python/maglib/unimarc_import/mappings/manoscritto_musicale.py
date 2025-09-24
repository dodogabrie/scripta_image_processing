# -*- coding: utf-8 -*-


from maglib.unimarc_import.base import\
    UnimarcBibAdder, CodeMap, UnimarcMapper, FunctionsMap
from maglib.unimarc_import.base_readers import ParentRelationIRMixin
from maglib.unimarc_import.readers import *


class ManoscrittoMusicaleMapper(UnimarcMapper):
    # forse obsoleto
    type = 'manoscritto musicale'
    def __init__(self, records_retriever, virtual_bid_tester):

        self._records_retriever = records_retriever
        self._virtual_bid_tester = virtual_bid_tester
        self._function_codes = FunctionsMap()
        super(ManoscrittoMusicaleMapper, self).__init__()

    def _build_readers(self):
        return (
            Type(),
            BibLevel(),
            Identifier(),

            Date100MSM(self._records_retriever),
            Language(),
            Title(),
            PublisherMSM(self._records_retriever),
            FormatMSM(),

            Description300MSM(),
            Description927(),

            Relation463MSM(self._virtual_bid_tester),
            RelationIR('464', "'comprende:' ",
                       self._virtual_bid_tester, repeat=True),
            UniformTitleMSM(),
            Relation517MSM(),
            Creator700_701(self._records_retriever, '700'),
            Creator700_701(self._records_retriever, '701'),
            Contributor702(self._records_retriever, self._function_codes),
            Contributor712(self._records_retriever, self._function_codes),

            )

    def _global_info_fix(self, info_value):
        info_value = re.sub(r',([^ ])', r', \1', info_value)
        return info_value


class Date100MSM(ParentFallbackIRMixin, Date100):
    def __init__(self, records_retriever):
        ParentFallbackIRMixin.__init__(self, records_retriever)
        Date100.__init__(self)
        self._level_reader = BibLevel()

    def read(self, marc_record):
        readed = self._read_not_fallback(marc_record)
        if readed:
            return readed
        record_level = self._level_reader.read(marc_record)[0]
        if record_level == 'a':
            return ParentFallbackIRMixin.read(self, marc_record)
        return []

    def _read_not_fallback(self, marc_record):
        return Date100.read(self, marc_record)


class PublisherMSM(ParentFallbackIRMixin, BasePublisher):
    def _read_not_fallback(self, marc_record):
        sf_a, sf_c, sf_e, sf_g = self._read_subfields_aceg(marc_record['210'])

        part1 = ' : '.join(filter(None, (sf_a, sf_c)))
        if part1:
            part1 = self._balance_part1_final_parenthesis(marc_record, part1)
        if not part1:
            return []
        if self._use_210d(marc_record):
            part2 = self._read_210d(marc_record)
        else:
            part2 = ''

        value = ', '.join(filter(None, (part1, part2)))
        if value:
            return [self._clean_value(value)]
        return []

    def _read_subfields(self, field, sf_n):
        readed = super(PublisherMSM, self)._read_subfields(field, sf_n)
        if sf_n != 'a':
            return readed
        return [ re.sub('^: ', '', r) for r in readed ]


class FormatMSM(MultiSubFieldsIR):
    def __init__(self):
        super(FormatMSM, self).__init__(
            'format', '215', ('a', 'd', 'e'), '', ' ; ')

    def _read_subfield(self, field, subfield_n):
        # aggiunge eventualemte ": $c" a quanto letto da $a
        if subfield_n == 'a':
            if field['c']:
                if field['a']:
                    return '%s : %s' % (field['a'], field['c'])
                return field['c']
        return super(FormatMSM, self)._read_subfield(field, subfield_n)

class Description300MSM(Description300):
    # aggiunge i dati dal campo 923
    def __init__(self):
        super(Description300MSM, self).__init__()
        self._923_reader = Description923MSM()

    def read(self, marc_record):
        readed = super(Description300MSM, self).read(marc_record)
        readed = readed[0] if readed else None
        readed_923 = self._923_reader.read(marc_record)
        readed_923 = readed_923[0] if readed_923 else None
        values = filter(None, (readed, readed_923))
        if not values:
            return [ ]
        return [ ' ; '.join(values) ]

class Description923MSM(MultiSubFieldsIR):
    def __init__(self):
        super(Description923MSM, self).__init__(
            'description', '923', ('i', 'c', 'l', 'h', 'm'), '', ' ; ',
            strip_sf_spaces=True)

    def _read_subfield(self, field, subfield_n):
        readed = super(Description923MSM, self)._read_subfield(
            field, subfield_n)
        if readed and subfield_n == 'c':
            if readed == 'S':
                return 'composito'
            return None
        if readed and subfield_n == 'm':
            readed = re.sub(r'\bres-?($|\W)', r'restaurato\1', readed, flags=re.I)
            readed = re.sub(r'\bmut-?($|\W)', r'mutilo\1', readed, flags=re.I)
        if readed and subfield_n == 'l':
            return '%s: %s' % ('legatura', readed)
        return readed

class Relation463MSM(ParentRelationIRMixin, RelationIR):
    def __init__(self, virtual_bid_tester):
        RelationIR.__init__(self, '463', "'fa parte di:' ", virtual_bid_tester)
    def read(self, marc_record):
        if self._field_463_rel_type(marc_record) != self.ASCENDING_RELATION:
            return []
        return RelationIR.read(self, marc_record)

class UniformTitleMSM(InfoReader):
    info_name = 'relation'
    def __init__(self):
        super(UniformTitleMSM, self).__init__()
        self._500_reader = SingleSubFieldIR('relation', '500', 'a')
        self._928_reader = UniformTitle928MSM()
        self._929_reader = UniformTitle929MSM()

    def read(self, marc_record):
        r_500 = self._500_reader.read(marc_record)
        r_928 = self._928_reader.read(marc_record)
        r_929 = self._929_reader.read(marc_record)

        r_500 = r_500[0] if r_500 else None
        r_928 = r_928[0] if r_928 else None
        r_929 = r_929[0] if r_929 else None

        first_part = '. '.join(filter(None, (r_500, r_928)))
        value = '. op. '.join(filter(None, (first_part, r_929)))
        if value:
            return [ '%s%s' % ("'titolo uniforme:' ", value) ]
        return []

class UniformTitle928MSM(MultiSubFieldsIR):
    def __init__(self):
        super(UniformTitle928MSM, self).__init__(
            'relation', '928', ('a', 'c'), '', '. ', strip_sf_spaces=True)
        self._musical_form_map = MusicalFormMap()

    def _read_subfield(self, field, subfield_n):
        if subfield_n == 'a':
            fields = field.get_subfields('a')
            values = [ self._musical_form_map.get(f.strip()) for f in fields ]
            values = filter(None, values)
            return ' '.join(values)
        return super(UniformTitle928MSM, self)._read_subfield(
            field, subfield_n)


class UniformTitle929MSM(MultiSubFieldsIR):
    def __init__(self):
        super(UniformTitle929MSM, self).__init__(
            'relation', '929', ('b', 'a', 'f', 'e', 'c', 'd'),
            strip_sf_spaces=True)
        self._musical_tones_map = MusicalTonesMap()

    def _read_subfield(self, field, subfield_n):
        readed = super(UniformTitle929MSM, self)._read_subfield(
            field, subfield_n)
        if readed and subfield_n == 'e':
            try:
                return self._musical_tones_map[readed]
            except KeyError:
                return None
        return readed

class Relation517MSM(MultiSubFieldsIR):
    def __init__(self):
        super(Relation517MSM, self).__init__(
            'relation', '517', ('a',), repeat=True)
        self._incipit_reader = MultiSubFieldsIR(
            'relation', '517', ('a',), prefix="'incipit testuale:' ")
        self._alt_title_reader = MultiSubFieldsIR(
            'relation', '517', ('a',), prefix="'titolo alternativo:' ")

    def _read_field(self, field):
        if field['e'] == 'I':
            return self._incipit_reader._read_field(field)
        elif field['e'] == 'T':
            return self._alt_title_reader._read_field(field)
        return ''

class Description927(MultiSubFieldsIR):
    def __init__(self):
        super(Description927, self).__init__(
            'description', '927', ('a', 'b'), separator=', ', repeat=True)

    def read(self, marc_record):
        readed = super(Description927, self).read(marc_record)
        if readed:
            readed = [ 'Personaggi: ' + ' ; '.join(filter(None, readed)) ]
        return readed

class MusicalFormMap(CodeMap):
    """tabella FOMU dei codici UNIMARC
    cfr http://www.iccu.sbn.it/opencms/export/sites/iccu\
    /documenti/2011/TB_CODICI.pdf"""
    file_name = 'musical_forms'

class MusicalTonesMap(CodeMap):
    """tabella TONO dei codici UNIMARC"""
    file_name = 'musical_tones'

