# -*- coding: utf-8 -*-

from maglib.unimarc_import.base import CodeMap
from maglib.unimarc_import.base_readers import InfoReader
from maglib.unimarc_import.readers import Description300, Format

from maglib.unimarc_import.mappings.moderno import ModernoMapper
from maglib.unimarc_import.mappings.antico import Description300Antico


class MappeMapper(ModernoMapper):
    """mappatura per le mappe geografiche"""
    def _build_readers(self):
        readers = list(super(MappeMapper, self)._build_readers())

        for i, r in enumerate(readers):
            if isinstance(r, Description300Antico):
                readers[i] = Description300_123Mappe()
        for i, r in enumerate(readers):
            if isinstance(r, Format):
                readers[i] = FormatMappe()

        return tuple(readers)


class Description123Mappe(InfoReader):
    info_name = 'description'
    def __init__(self):
        super(Description123Mappe, self).__init__()
        self._scale_type_indicator_map = ScaleTypeIndicatorMap()
        self._scale_type_map = ScaleTypeMap()

    def read(self, marc_record):
        f = marc_record['123']
        if not f:
            return []
        values = []
        try:
            values.append(self._scale_type_indicator_map[f.indicators[0]])
        except KeyError:
            pass
        try:
            values.append(self._scale_type_map[f['a']])
        except KeyError:
            pass
        if values:
            return [ ', '.join(values) ]
        return []


class Description300_123Mappe(InfoReader):
    """legge una description dai campi 300 e 123"""
    info_name = 'description'
    def __init__(self):
        super(Description300_123Mappe, self).__init__()
        self._desc_300_reader = Description300()
        self._desc_123_reader = Description123Mappe()

    def read(self, marc_record):
        desc_123_r = self._desc_123_reader.read(marc_record)
        desc_123_r = desc_123_r[0] if desc_123_r else ''
        desc_300_r = self._desc_300_reader.read(marc_record)
        desc_300_r = desc_300_r[0] if desc_300_r else ''

        readed = filter(None, (desc_123_r, desc_300_r))
        if not readed:
            return []
        value = ' ; '.join(readed)
        return [ value[0].upper() + value[1:] ]


class Format121Mappe(InfoReader):
    info_name = 'format'
    # cfr. http://www.iccu.sbn.it/opencms/export/sites/iccu\
    #    /documenti/2011/TB_CODICI.pdf
    def __init__(self):
        super(Format121Mappe, self).__init__()
        self._dimension_map = DimensionMap()
        self._physical_support_map = PhysicalSupportMap()
        self._techinique_map = TechniqueMap()
        self._reproduction_form_map = ReproductionFormMap()

    def read(self, marc_record):
        f = marc_record['121']
        if not f or not f['a']:
            return []
        values = []
        for rng, code_map in (
            ((0, 1), self._dimension_map),
            ((3, 5), self._physical_support_map),
            ((5, 6), self._techinique_map),
            ((6, 7), self._reproduction_form_map)):
            try:
                data = f['a'][rng[0]: rng[1]]
                values.append(code_map[data])
            except KeyError:
                pass
        if values:
            uniq_values = []
            for v in values:
                if not v in uniq_values:
                    uniq_values.append(v)
            return [ ' ; '.join(uniq_values) ]
        return []


class FormatMappe(Format):
    def __init__(self):
        self._fmt_121_reader = Format121Mappe()
        self._reading_record = None
        super(FormatMappe, self).__init__()

    def read(self, marc_record):
        self._reading_record = marc_record
        return super(FormatMappe, self).read(marc_record)

    def _read_subfield(self, field, subfield_n):
        readed = super(FormatMappe, self)._read_subfield(field, subfield_n)
        if subfield_n == 'a':
            assert self._reading_record
            readed_121 = self._fmt_121_reader.read(self._reading_record)
            if readed_121:
                readed += ' : %s' % readed_121[0]
        return readed

class ScaleTypeIndicatorMap(CodeMap):
    """tabella TISC dei codici UNIMARC
    cfr http://www.iccu.sbn.it/opencms/export/sites/iccu\
    /documenti/2011/TB_CODICI.pdf"""
    file_name = 'scale_type_indicator'

class ScaleTypeMap(CodeMap):
    """tabella SCAL dei codici UNIMARC"""
    file_name = 'scale_type'

class DimensionMap(CodeMap):
    """tabella DIME dei codici UNIMARC"""
    file_name = 'dimension'

class PhysicalSupportMap(CodeMap):
    """tabella SUFC dei codici UNIMARC"""
    file_name = 'cartographic_physical_support'

class TechniqueMap(CodeMap):
    """tabella TECN dei codici UNIMARC"""
    file_name = 'cartographic_technique'

class ReproductionFormMap(CodeMap):
    """tabella FORI dei codici UNIMARC"""
    file_name = 'reproduction_form'



