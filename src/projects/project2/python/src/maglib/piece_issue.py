# -*- coding: utf-8 -*-

"""Questo modulo contiene gli strumenti per gestire la sezione piece del mag
secondo le indicazioni ICCU PIECE 1.5 per i periodici"""

import datetime
import logging
import re

logger = logging.getLogger('piece_issue')


class Attrs_container(object):
    """oggetto che contiene degli attributi di classi diverse"""
    # mappatura nome attributo -> classe
    attrs_classes = {}

    def __init__(self, **kwargs):
        super(Attrs_container, self).__setattr__(
            '_attrs', self.attrs_classes.keys())
        for attr in self._attrs:
            setattr(self, attr, None)

        for arg, value in kwargs.items():
            if not arg in self._attrs:
                continue
            setattr(self, arg, value)

    def __setattr__(self, name, value):
        if ( not name in self._attrs or
             isinstance(value, self.attrs_classes[name]) or
             value is None ):
            return super(Attrs_container, self).__setattr__(name, value)
        Class = self.attrs_classes[name]
        if isinstance(value, tuple):
            attr = Class(*value)
        else:
            attr = Class(value)
        return super(Attrs_container, self).__setattr__(name, attr)

    def __repr__(self):
        name = self.__class__.__name__
        attrs = ', '.join([ '%s=%s' % (attr, repr(getattr(self, attr)))
                  for attr in self._attrs ])
        return '%s(%s)' % (name, attrs)


class Attr_error(Exception):
    def __init__(self, attr_name):
        self._name = attr_name


class Attr_parse_error(Attr_error):
    def __init__(self, attr_name, string):
        super(Attr_parse_error, self).__init__(attr_name)
        self._string = string

    def __str__(self):
        return 'error parsing attr %s from string %s' % (
            self._name, self._string)


class Attr_value_error(Attr_error):
    def __init__(self, attr_name, value):
        super(Attr_value_error, self).__init__(attr_name)
        self._value = value

    def __str__(self):
        return 'invalid value %s for attr %s' % (self._value, self._name)


class Issue_info_attr(object):
    """uno degli attributi che compone le informazioni su un fascicolo"""
    def __init__(self, value):
        self._value = value

    @property
    def name(self):
        """il nome dell'attributo"""
        raise NotImplementedError()

    @classmethod
    def from_string(cls, s):
        """costruisce l'attributo dalla stringa :s:"""
        raise NotImplementedError()

    @classmethod
    def from_issue_component(cls, s):
        """costruisce l'attributo dalla stringa :s:, che è un componente
        della stringa <issue> del mag."""
        raise NotImplementedError()

    @property
    def value(self):
        """il valore dell'attributo in formato grezzo"""
        return self._value

    def __str__(self):
        """ritorna la rappresentazione di questo attributo come stringa"""
        raise NotImplementedError()

    def as_issue_component(self):
        """ritorna la stringa rappresentazione di questo attributo in
        <issue>"""
        raise NotImplementedError()

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, self._value)

    def copy(self):
        """restituisce un attributo copia di questo"""
        raise NotImplementedError()


class Issue_num_attr(Issue_info_attr):
    """un attributo numero intero"""
    def __init__(self, value):
        if not isinstance(value, int):
            raise Attr_value_error(self.name, value)
        self._value = int(value)

    @classmethod
    def from_string(cls, s):
        try:
            return cls(int(s))
        except (ValueError, TypeError):
            raise Attr_parse_error(cls.name, s)

    @classmethod
    def from_issue_component(cls, s):
        m = re.match(r'^%s (\d+)$' % cls._component_prefix, s)
        if not m:
            raise Attr_parse_error(cls.name, s)
        return cls(int(m.group(1)))

    def __str__(self):
        return '%d' % self._value

    def as_issue_component(self):
        return '%s %d' % (self._component_prefix, self._value)

    def copy(self):
        return self.__class__(self._value)

    @property
    def _component_prefix(self):
        # prefisso che ha l'attributo quando è componente nella stringa <issue>
        raise NotImplementedError()


class Issue_range_attr(Issue_num_attr):
    """un attributo che è un numero intero o una coppia di numeri interi"""
    def __init__(self, *values):
        if len(values) in (1, 2):
            try:
                if len(values) == 1:
                    self._value = int(values[0])
                elif len(values) == 2:
                    self._value = (int(values[0]), int(values[1]))
                return
            except (TypeError, ValueError):
                pass
        raise Attr_value_error(self.name, values)

    @classmethod
    def from_string(cls, s):
        try:
            return Issue_num_attr.from_string.__func__(cls, s)
        except Attr_parse_error:
            pass
        m = re.match(r'^\s*(\d+)\s*-\s*(\d+)\s*$', s)
        if m:
            try:
                return cls(int(m.group(1)), int(m.group(2)))
            except Attr_value_error:
                pass
        raise Attr_parse_error(cls.name, s)

    def __str__(self):
        if self.has_range_value():
            return '%d-%d' % self._value
        return '%d' % self._value

    @classmethod
    def from_issue_component(cls, s):
        try:
            return super(Issue_range_attr, cls).from_issue_component(s)
        except Attr_parse_error:
            m = re.match(r'^%s (\d+)-(\d+)' % cls._component_prefix, s)
            if m:
                return cls(m.group(1), m.group(2))
            raise Attr_parse_error(cls.name, s)

    def as_issue_component(self):
        if self.has_range_value():
            return '%s %d-%d'% (self._component_prefix,
                                self._value[0], self._value[1])
        return super(Issue_range_attr, self).as_issue_component()

    def has_range_value(self):
        """dice se il valore di questo attributo è un range di numeri,
        altrimenti è un numero singolo"""
        return isinstance(self._value, tuple)

    def copy(self):
        if self.has_range_value():
            args = self._value
        else:
            args = (self._value,)
        return self.__class__(*args)


class Issue_num_free_attr(Issue_num_attr):
    """attributo che può essere espresso come numero o come forma libera"""

    def __init__(self, value):
        if not isinstance(value, (int, str)):
            raise Attr_value_error(self.name, value)
        self._value = value

    @classmethod
    def from_string(cls, s):
        if cls._freeform_regex.search(s):
            return cls(s)
        return super(Issue_num_free_attr, cls).from_string(s)

    @classmethod
    def from_issue_component(cls, s):
        try:
            return super(Issue_num_free_attr, cls).from_issue_component(s)
        except Attr_parse_error:
            if cls._freeform_regex.search(s):
                return cls(s)
            raise Attr_parse_error(cls.name, s)

    def __str__(self):
        return '%s' % self._value

    def as_issue_component(self):
        if isinstance(self._value, str):
            return self._value
        return '%s %d' % (self._component_prefix, self._value)

    def has_freeform_value(self):
        """dice se il valore di questo attributo è in formato libero o
        altrimenti in forma numerica"""

        return isinstance(self._value, str)

    @property
    def _freeform_regex(self):
        # ritorna la regex che deve rispettare il formato libero dell'attributo
        raise NotImplementedError()


class Issue_num_true_attr(Issue_num_attr):
    """attributo che può avere valore un numero o anche nessuno
    (solamente presente)"""
    def __init__(self, value=None):
        if value in (True, None):
            self._value = True
        else:
            super(Issue_num_true_attr, self).__init__(value)

    @classmethod
    def from_issue_component(cls, s):
        if s == cls._component_prefix:
            return cls()
        return super(Issue_num_true_attr, cls).from_issue_component(s)

    def has_true_value(self):
        """dice se l'attributo ha solo il valore "presenza" """
        return self._value is True

    def __str__(self):
        if self.has_true_value():
            raise Exception(
                'Attr %s has True value, don\'t ask string' % self.name)
        return super(Issue_num_true_attr, self).__str__()

    def as_issue_component(self):
        if self.has_true_value():
            return self._component_prefix
        return super(Issue_num_true_attr, self).as_issue_component()


class Issue_range_true_attr(Issue_range_attr):
    """un attributo che può avere valore un numero (o un range numerico)
    o anche nessun valore (solo presente)"""
    def __init__(self, *values):
        if not len(values) or (len(values) == 1 and (
                values[0] is True or values[0] is None)):
            self._value = True
        else:
            super(Issue_range_true_attr, self).__init__(*values)

    @classmethod
    def from_issue_component(cls, s):
        if s == cls._component_prefix:
            return cls()
        return super(Issue_range_true_attr, cls).from_issue_component(s)

    def has_true_value(self):
        return self._value is True

    def __str__(self):
        if self.has_true_value():
            raise Exception(
                'Attr %s has True value, don\'t ask string' % self.name)
        return super(Issue_range_true_attr, self).__str__()

    def as_issue_component(self):
        if self.has_true_value():
            return self._component_prefix
        return super(Issue_range_true_attr, self).as_issue_component()


class Year(Issue_range_attr):
    name = 'year'
    _component_prefix = 'A.'


class Volume(Issue_num_attr):
    name = 'volume'
    _component_prefix = 'vol.'


class Publ_year(Issue_range_attr):
    name = 'publ_year'

    def as_issue_component(self):
        # uso questo se publ_year è inserito poi nel mag in <year> e non <issue>
        return self.__str__()

    @classmethod
    def from_issue_component(cls, s):
        # non si legge da <issue>
        raise Attr_parse_error(cls.name, s)


class Month(Issue_range_attr):
    name = 'month'
    _index_months_map = dict(
        enumerate(('gen.', 'feb.', 'mar.', 'apr.', 'mag.', 'giu.',
                   'lug.', 'ago.', 'set.', 'ott.', 'nov.', 'dic.'), 1))
    _months_index_map = dict((v, k) for k, v in _index_months_map.items())

    def __init__(self, *values):
        super(Month, self).__init__(*values)
        for v in self._value if self.has_range_value() else (self._value,):
            if not (v >= 1 and v <= 12):
                raise Attr_value_error(self.name, v)

    @classmethod
    def from_issue_component(cls, s):
        month_index = cls._months_index_map.get(s)
        if month_index is not None:
            return cls(month_index)
        m = re.match(r'^(\w+\.)-(\w+\.)$', s)
        if m:
            first_month_index = cls._months_index_map.get(m.group(1))
            second_month_index = cls._months_index_map.get(m.group(2))
            if first_month_index is not None and \
                    second_month_index is not None:
                return cls(first_month_index, second_month_index)
        raise Attr_parse_error(cls.name, s)

    def as_issue_component(self):
        if self.has_range_value():
            return '%s-%s' % tuple(self._index_months_map.get(v)
                                   for v in self._value)
        return '%s' % self._index_months_map.get(self._value)


class Day(Issue_range_attr):
    name = 'day'

    def __init__(self, *values):
        super(Day, self).__init__(*values)
        for v in (self._value if self.has_range_value() else (self._value,)):
            if not (v >= 1 and v <= 31):
                raise Attr_value_error(self.name, v)

    @classmethod
    def from_issue_component(cls, s):
        try:
            return cls(int(s))
        except ValueError:
            pass
        m = re.match(r'^(\d+)-(\d+)$', s)
        if m:
            return cls(int(m.group(1)), int(m.group(2)))
        raise Attr_parse_error(cls.name, s)

    def as_issue_component(self):
        if self.has_range_value():
            return '%d-%d' % self._value
        return '%d' % self._value


class Edition(Issue_num_free_attr):
    name = 'edition'
    _component_prefix = 'ed.'
    _freeform_regex = re.compile(r'\bed\. ')


class Series(Issue_num_free_attr):
    name = 'series'
    _component_prefix = 'serie'
    _freeform_regex = re.compile(r'\bserie\b')


class Appendix(Issue_num_true_attr):
    name = 'appendix'
    _component_prefix = 'app.'


class Attachment(Issue_num_true_attr):
    name = 'attachment'
    _component_prefix = 'all.'


class Index(Issue_num_true_attr):
    name = 'index'
    _component_prefix = 'ind.'


class Supplement(Issue_range_true_attr):
    name = 'supplement'
    _component_prefix = 'suppl.'


class Issue_n(Issue_range_attr, Issue_num_free_attr):
    name = 'issue_n'
    _component_prefix = 'fasc.'
    _freeform_regex = re.compile('numero')
    def __init__(self, *values):
        if len(values) == 1:
            Issue_num_free_attr.__init__(self, values[0])
        else:
            Issue_range_attr.__init__(self, *values)

    @classmethod
    def from_string(cls, s):
        try:
            return Issue_range_attr.from_string.__func__(cls, s)
        except Attr_parse_error:
            return Issue_num_free_attr.from_string.__func__(cls, s)

    @classmethod
    def from_issue_component(cls, s):
        try:
            return Issue_num_free_attr.from_issue_component.__func__(cls, s)
        except Attr_parse_error:
            m = re.match(r'^%s (\d+)-(\d+)$' % cls._component_prefix, s)
            if m:
                return cls(*m.group(1, 2))
            raise Attr_parse_error(cls.name, s)

    def __str__(self):
        if self.has_range_value():
            return Issue_range_attr.__str__(self)
        return Issue_num_free_attr.__str__(self)

    def as_issue_component(self):
        if self.has_range_value():
            return '%s %d-%d' % (
                self._component_prefix, self._value[0], self._value[1])
        return Issue_num_free_attr.as_issue_component(self)

    def copy(self):
        return Issue_range_attr.copy.__func__(self)


class Repetition(Issue_num_attr):
    name = 'repetition'
    repetitions = ['bis', 'ter', 'quater', 'quinquies']

    def __init__(self, value):
        super(Repetition, self).__init__(value)
        if not self._value >= 2 and self._value <= 5:
            raise Attr_value_error()

    @classmethod
    def from_string(cls, s):
        try:
            return cls(int(s))
        except (Attr_value_error, ValueError):
            raise Attr_parse_error(cls.name, s)

    @classmethod
    def from_issue_component(cls, s):
        try:
            index = cls.repetitions.index(s)
            return cls(index + 2)
        except (Attr_value_error, ValueError):
            raise Attr_parse_error(cls.name, s)

    def as_issue_component(self):
        return self.repetitions[self._value - 2]


class Issue_info(Attrs_container):
    """le informazioni bibliografiche su di un singolo fascicolo di
    un periodico"""
    attrs_classes = {
        'publ_year': Publ_year,   # n oppure (n, m)
        'month': Month,           # n oppure (n, m)
        'day': Day,               # n oppure (n, m)
        'year': Year,             # n
        'issue_n': Issue_n,       # n oppure (n, m) oppure "numero unico", etc ...

        'edition': Edition,       # n oppure "ed. speciale", etc ...
        'series': Series,         # n oppure "serie nuova", etc ...
        'volume': Volume,         # n

        'appendix': Appendix,     # True oppure n
        'attachment': Attachment, # True oppure n
        'index': Index,           # True oppure n
        'supplement': Supplement, # True oppure n

        'repetition': Repetition  # n, 2 = bis, 3 = ter, etc...
        }

    @classmethod
    def build_from_piece(cls, piece):
        """costruisce un nuovo oggetto da un elemento piece del mag"""
        if piece.issue.get_value():
            info = cls.from_issue_string(piece.issue.get_value())
        else:
            info = cls()
        try:
            info.publ_year = Publ_year.from_string(piece.year.get_value() or '')
        except Attr_parse_error:
            pass
        return info

    @classmethod
    def from_issue_string(cls, issue_string):
        """costruisce un nuovo oggetto dalla stringa <issue> del mag
        L'oggetto non comprende publ_year, scritto in <year>"""
        issue_info = cls()
        for component in [ c for c in issue_string.split(', ')]:
            readed = False
            for attr, Class in cls.attrs_classes.items():
                try:
                    setattr(issue_info, attr,
                            Class.from_issue_component(component))
                except Attr_parse_error:
                    continue
                else:
                    readed = True
                    break
            if not readed:
                logger.warn('Ignoring piece component %s' % component)
        return issue_info

    def copy_values(self, issue_info):
        """copia le informazioni presenti in un altro Issue_info
        in questo Issue_info.
        :param Issue_info issue_info:"""
        for attr in self._attrs:
            if getattr(issue_info, attr) is not None:
                setattr(self, attr, getattr(issue_info, attr).copy())

    def apply_to_piece(self, piece, numeration_min_ciphers=None):
        """copia le informazioni in elemento piece del mag
        :numeration_min_ciphers: se diverso da None, dizionario con i numeri
        minimi di cifre per volume, year, issue_n, edition nel codice SICI"""
        if self.publ_year is not None:
            piece.year.set_value(str(self.publ_year))
        else:
            piece.year.set_value(None)

        piece.issue.set_value(self.as_issue_string())
        piece.stpiece_per.set_value(
            Sici_code.from_issue(self, numeration_min_ciphers))

    def as_issue_string(self):
        components = []
        for attr in ('year', 'month', 'day', 'issue_n', 'edition', 'series',
                     'volume', 'appendix', 'attachment', 'index', 'supplement',
                     'repetition'):
            if getattr(self, attr) is not None:
                components.append(getattr(self, attr).as_issue_component())

        return ', '.join(components)

    def next_issue_info(self):
        """ritorna le informazioni calcolate per l'issue successivo a questo"""
        # TODO: capire come creare informazioni adeguate anche quando si usano
        # valori range
        info = Issue_info()
        if (not None in (self.publ_year, self.month,  self.day)):
            self._copy_next_day_info(self, info)

        elif not None in (self.publ_year, self.month) and \
                not self.publ_year.has_range_value() and \
                not self.month.has_range_value():
            if self.month.value == 12:
                info.month = Month(1)
                info.publ_year = Publ_year(self.publ_year.value + 1)
            else:
                info.publ_year = self.publ_year.copy()
                info.month = Month(self.month.value + 1)
        elif self.publ_year is not None and \
                not self.publ_year.has_range_value():
            info.publ_year = Publ_year(self.publ_year.value + 1)

        for attr in ('year', 'series', 'volume'):
            if getattr(self, attr) is not None:
                setattr(info, attr, getattr(self, attr).copy())

        if self.issue_n is not None and \
                not self.issue_n.has_range_value() and \
                not self.issue_n.has_freeform_value():
            info.issue_n = Issue_n(self.issue_n.value + 1)

        return info

    @classmethod
    def _next_day(cls, year, month, day):
        # ritorna (year, month, day) del giorno successivo
        date = datetime.date(year, month, day)
        next_day_date = date + datetime.timedelta(days=1)
        return next_day_date.year, next_day_date.month, next_day_date.day

    @classmethod
    def _copy_next_day_info(cls, src_info, dst_info):
        # copia le informazioni sulla data (giorno, mese, anno pubblicazione)
        # da src_info a dst_info, aumentando di uno il giorno solare.
        # le informazioni in src_info devono essere complete
        # se il giorno di src_info è un range, dst_info avrà il giorno
        if None in (src_info.publ_year, src_info.month, src_info.day):
            return

        if src_info.day.has_range_value():
            # 14-15 -> 15-16
            try:
                src_month = (src_info.month.value[0] if
                             src_info.month.has_range_value() else
                             src_info.month.value)
                next_day = cls._next_day(src_info.publ_year.value, src_month,
                                         src_info.day.value[0])
            except ValueError as exc:
                return
            next_next_day = cls._next_day(*next_day)
            if next_day[0] == next_next_day[0]:
                dst_info.publ_year = Publ_year(next_day[0])
            else:
                dst_info.publ_year = Publ_year(next_day[0], next_next_day[0])
            if next_day[1] == next_next_day[1]:
                dst_info.month = Month(next_day[1])
            else:
                dst_info.month = Month(next_day[1], next_next_day[1])
            dst_info.day = Day(next_day[2], next_next_day[2])
            return

        try:
            # 14 -> 15
            next_day = cls._next_day(
                src_info.publ_year.value, src_info.month.value,
                src_info.day.value)
        except ValueError:
            return
        dst_info.publ_year  = Publ_year(next_day[0])
        dst_info.month = Month(next_day[1])
        dst_info.day = Day(next_day[2])


class Sici_code(object):
    """classe che genera la string SICI nella sintassi usata dal mag"""

    @classmethod
    def from_issue(cls, issue_info, n_ciphers=None):
        """ritorna la stringa sici proveniente da :issue_info:
        :n_ciphers: se diverso da None, un dizionario con i numeri minimi
        di cifre per volume/year/issue_n/edition"""
        chrono = cls._as_sici_chrono_string(issue_info)

        if not n_ciphers:
            n_ciphers = dict((a, 1) for a in (
                'volume', 'year', 'issue_n', 'edition'))
        num = cls._as_sici_num_string(issue_info, n_ciphers)

        if issue_info.supplement is not None:
            suffix = '+'
        elif issue_info.index is not None:
            suffix = '*'
        else:
            suffix = ''
        return '(%s)%s%s' % (chrono, num, suffix)

    @classmethod
    def _as_sici_chrono_string(cls, issue_info):
        # ritorna le informazioni cronologiche sul fascicolo nella sintassi
        # SICI usata dal mag
        i = issue_info

        if i.publ_year is not None and i.month is not None and \
                i.publ_year.has_range_value() and i.month.has_range_value():
            return '%04d%02d/%04d%02d' % (
                i.publ_year.value[0], i.month.value[0],
                i.publ_year.value[1], i.month.value[1])

        if i.publ_year is None:
            chrono_s = '0000'
        elif i.publ_year.has_range_value():
            chrono_s = '%04d/%04d' % i.publ_year.value
        else:
            chrono_s = '%04d' % i.publ_year.value

        if i.month is None:
            chrono_s += '00'
        elif i.month.has_range_value():
            chrono_s += '%02d/%02d' % i.month.value
        else:
            chrono_s += '%02d' % i.month.value

        if not '/' in chrono_s:
            if i.day is None:
                chrono_s += '00'
            elif i.day.has_range_value():
                chrono_s += '%02d/%02d' % i.day.value
            else:
                chrono_s += '%02d' % i.day.value
        return chrono_s

    @classmethod
    def _as_sici_num_string(cls, issue_info, n_ciphers):
        i = issue_info
        nums = []
        if i.year is not None:
            if i.year.has_range_value():
                # il range nella prima posizione della numerazione è permessa
                # dallo standard SICI ma vietata da MAG, per cui inserisco solo
                # il primo valore
                # nums.append('%0*d/%0*d' % (
                #         n_ciphers['year'], i.year.value[0],
                #         n_ciphers['year'], i.year.value[1]))
                nums.append('%0*d' % (n_ciphers['year'], i.year.value[0]))
            else:
                nums.append('%0*d' % (n_ciphers['year'], i.year.value))
        elif i.volume is not None:
            nums.append('%0*d' % (n_ciphers['volume'], i.volume.value))
        else:
            nums.append('%0*d' % (n_ciphers['volume'], 0))

        if i.issue_n is None or i.issue_n.has_freeform_value():
            nums.append('%0*d' % (n_ciphers['issue_n'], 0))
        elif i.issue_n.has_range_value():
            nums.append('%0*d/%0*d' % (
                    n_ciphers['issue_n'], i.issue_n.value[0],
                    n_ciphers['issue_n'], i.issue_n.value[1]))
        else:
            nums.append('%0*d' % (n_ciphers['issue_n'], i.issue_n.value))

        if i.edition and not i.edition.has_freeform_value():
            nums.append('%0*d' % (n_ciphers['edition'], i.edition.value))
        if i.repetition:
            if len(nums) == 2:
                nums.append('%0*d' % (n_ciphers['edition'], 0))
            nums.append(str(i.repetition))

        return ':'.join(nums)
