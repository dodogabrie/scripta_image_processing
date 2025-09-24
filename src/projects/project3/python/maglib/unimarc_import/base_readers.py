# -*- coding: utf-8 -*-

import os
import re


class InfoReadException(Exception):
    pass


class InfoReader(object):
    """legge una singola informazione dal record unimarc"""

    info_name = ""

    def __init__(self, info_name=None):
        """:info_name: se diverso da Noneil nome dell'informazione che verrà
        letta, altrimenti il nome dell'informazione sarà preso dall'attributo
        di classe"""
        if info_name is not None:
            self.info_name = info_name

    def read(self, marc_record):
        """legge l'informazione e ritorna la lista di valori letti
        :marc_record: pymarc.record.Record da cui leggere le informazioni"""
        raise NotImplementedError()

    def _decode_string(self, s):
        # codifica la stringa dal formato marc
        # si incontrano alcuni unimarc non in utf-8 nonostante sia control
        # lo standard
        if not isinstance(s, str):
            encoding = os.environ.get("MARC_CHAR_ENCODING") or "utf-8"
            s = s.decode(encoding)
        return s

    def _clean_value(self, v):
        # leva "il di più" dal valore letto
        return self._decode_string(v).strip()

    def _clean_values(self, values):
        # pulisce una serie di valori letti
        return [self._clean_value(v) for v in values]


class SingleSubFieldIR(InfoReader):
    def __init__(self, info_name, field_n, subfield_n, prefix="", repeat=False):
        """:field_n: numero del campo unimarc da cui estrarre l'informazione
        :subfield_n: sottocampo da cui estrarre l'informazione
        :prefix: prefisso per quanto estratto
        :repeat: se vero, leggi un valore per ogni campo unimarc
        field_n presente"""
        super(SingleSubFieldIR, self).__init__(info_name)
        self._field_n = field_n
        self._subfield_n = subfield_n
        self._prefix = prefix
        self._repeat = repeat

    def read(self, marc_record):
        values = []
        fields = marc_record.get_fields(self._field_n)
        if not self._repeat:
            fields = fields[:1] if fields else []

        for field in fields:
            subfield = field[self._subfield_n]
            if subfield:
                value = "%s%s" % (self._prefix, self._decode_string(subfield))
                values.append(value)
        return self._clean_values(values)


class MultiSubFieldsIR(InfoReader):
    def __init__(
        self,
        info_name,
        field_n,
        subfields_ns,
        prefix="",
        separator="",
        repeat=False,
        strip_sf_spaces=False,
        collapse_spaces=True,
    ):
        """:strip_sf_spaces: elimina gli spazi iniziali e finali da ciascun
        sottocampo prima di unirli
        :collapse_space: sostituisci ogni sequenza di spazi bianchi con una
        spazio"""
        super(MultiSubFieldsIR, self).__init__(info_name)
        self._field_n = field_n
        self._subfields_ns = subfields_ns
        self._prefix = prefix
        self._separator = separator
        self._repeat = repeat
        self._strip_sf_spaces = strip_sf_spaces
        self._collapse_spaces = collapse_spaces

    def read(self, marc_record):
        values = []
        fields = marc_record.get_fields(self._field_n)
        if not self._repeat:
            fields = fields[:1] if fields else []
        for field in fields:
            readed = self._read_field(field)
            if readed is not None:
                values.append(readed)
        return values

    def _read_field(self, field):
        subfields = filter(
            None,
            [
                self._read_subfield(field, subfield_n)
                for subfield_n in self._subfields_ns
            ],
        )
        subfields = [self._decode_string(sf) for sf in subfields if sf]
        if not subfields:
            return None
        value = self._prefix + self._separator.join(subfields)
        return self._clean_value(value)

    def _read_subfield(self, field, subfield_n):
        v = field[subfield_n]
        if v and self._strip_sf_spaces:
            v = v.strip()
        return v

    def _clean_value(self, v):
        v = super(MultiSubFieldsIR, self)._clean_value(v)
        if self._collapse_spaces:
            v = re.sub(r" {2,}", " ", v).strip()
        return v

    def _read_subfields(self, field, subfield_n):
        values = []
        for sf in field.get_subfields(subfield_n):
            value = self._clean_value(sf)
            if value:
                values.append(value)
        return values


class ParentRelationIRMixin(object):
    """lettore di informazioni che considera l'eventuale relazione con un
    bid di livello superiore"""

    ASCENDING_RELATION = 1
    DESCENDING_RELATION = 2

    def _parent_bid(self, marc_record):
        """ritorna il bid "padre" del bid descritto dal record"""
        rel_field = self._first_relation_field(marc_record)
        if not rel_field:
            return None
        return re.sub(r"^001", "", rel_field["1"])

    def _first_relation_field(self, marc_record):
        """il primo campo di relazione gerarchica verso il genitore trovato,
        o None se non c'è"""
        for c in (1, 2):
            field = marc_record["46%d" % c]
            if field:
                return field
        # il campo 463 è una relazione al genitore solo se
        # sono vere condizioni aggiuntive
        if (
            marc_record["463"]
            and self._field_463_rel_type(marc_record) == self.ASCENDING_RELATION
        ):
            return marc_record["463"]
        return None

    def _work_is_part(self, marc_record):
        """dice se se il record unimarc descrive un'opera che è parte di
        altre opere"""
        title_field = marc_record["200"]
        if not title_field or not title_field["a"]:
            return False
        if self._first_relation_field(marc_record) is None:
            return False
        return re.match(r"^\s*(?:tomo|parte)?\s*(\d+)\W*$", title_field["a"], re.I)

    def _field_463_rel_type(self, marc_record):
        """dice se il campo 463 esprime una relazione ascendente (1),
        discendente (2) o nessuna"""
        ldr = marc_record.leader
        if ldr[7] == "a":
            return self.ASCENDING_RELATION
        if ldr[7] == "m" and ldr[8] in ("1", "2"):
            return self.DESCENDING_RELATION
        return None


class ParentFieldsFallbackIRMixin(ParentRelationIRMixin):
    """lettore di informazioni che delega la ricerca di campi e sottocampi
    al record unimarc del bid di livello superiore se l'informazione
    non è presente in quello del record"""

    def __init__(self, records_retriever):
        """:records_retriever: RecordsRetriever"""
        self._id_reader = Identifier()
        self._records_retriever = records_retriever
        # coppia bid corrente, unimarc genitore
        self._current_bid_parent = (None, None)

    def _read_field_fallback(self, marc_record, field_n):
        """ottiene un campo unimarc :field_n:, dal record :marc_record: o
        se non presente ricorsivamente dai record dei bid di livello superiore
        collegati da relazioni gerarchiche presenti nel record"""
        f = marc_record[field_n]
        if f:
            return f
        parent_record = self._parent_unimarc(marc_record)
        if not parent_record:
            return None
        # ricorsivo :
        return self._read_field_fallback(parent_record, field_n)
        # return parent_record[field_n]

    def _read_subfields_fallback(self, marc_record, field_n, subfield_n):
        """ottiene un sottocampo unimarc :subfield_n: del campo :field_n:,
        dal record :marc_record: o se non presente ricorsivamente dai record
        dei bid di livello superiore collegati da relazioni gerarchiche presenti
        nel record"""
        f = marc_record[field_n]
        if f:
            subfields = f.get_subfields(subfield_n)
            if subfields:
                return subfields

        parent_record = self._parent_unimarc(marc_record)
        if not parent_record:
            return None
        return self._read_subfields_fallback(parent_record, field_n, subfield_n)

    def _read_subfield_fallback(self, marc_record, field_n, subfield_n):
        subfields = self._read_subfields_fallback(marc_record, field_n, subfield_n)
        return subfields[0] if subfields else None

    def _parent_unimarc(self, marc_record):
        bid = self._id_reader.read(marc_record)[0]
        if self._current_bid_parent[0] == bid and self._current_bid_parent[1]:
            return self._current_bid_parent[1]

        parent_bid = self._parent_bid(marc_record)
        if not parent_bid:
            return None
        parent_marc = self._records_retriever.get_record(parent_bid)
        if not parent_marc:
            return None
        self._current_bid_parent = (bid, parent_marc)
        return parent_marc


class ParentFallbackIRMixin(ParentRelationIRMixin):
    """lettore di informazioni che delega completamente la ricerca al
    record unimarc del bid di livello superiore se l'informazione
    non è presente"""

    def __init__(self, records_retriever):
        """:records_retriever: RecordsRetriever"""
        self._records_retriever = records_retriever

    def read(self, marc_record):
        """do NOT override. override self._read_not_fallback"""
        readed = self._read_not_fallback(marc_record)
        if readed:
            return readed
        parent_bid = self._parent_bid(marc_record)
        if not parent_bid:
            return []
        parent_record = self._records_retriever.get_record(parent_bid)
        if not parent_record:
            msg = "Can't find record for parent %s" % parent_bid
            raise InfoReadException(msg)
        return self.read(parent_record)

    def _read_not_fallback(self, marc_record):
        raise NotImplementedError()


class MultiSubFieldsFallbackIR(ParentFallbackIRMixin, MultiSubFieldsIR):
    def __init__(
        self,
        records_retriever,
        info_name,
        field_n,
        subfield_ns,
        prefix="",
        separator="",
        repeat=False,
    ):
        ParentFallbackIRMixin.__init__(self, records_retriever)
        MultiSubFieldsIR.__init__(
            self, info_name, field_n, subfield_ns, prefix, separator, repeat
        )

    def _read_not_fallback(self, marc_record):
        return MultiSubFieldsIR.read(self, marc_record)


class TitleReaderMixin(object):
    """mixin per i lettori che leggono un titolo, che a volte ha
    caratteri strani"""

    @classmethod
    def _clean_value(self, v):
        v = re.sub(r"[\x88\x89\x98\x9c\x0e]", "", v)
        # v = re.sub(ur'[\u2117]', '', v, flags=re.UNICODE)
        v = re.sub(r"\x1b[HI]", "", v)
        v = re.sub(r"\\([\d\-]+)!", r"[\1]", v)
        v = v.replace("*", "")
        v = v.replace("<<", "")
        v = v.replace(">>", "")
        v = re.sub(r" {2,}", " ", v).strip()
        return v


class BidReferenceIRMixin(object):
    """lettore di informazioni che ha riferimento a un bid esterno, che può
    essere concreto (digitalizzato) o virtuale"""

    def __init__(self, virtual_bid_tester):
        """:virtual_bid_tester: VirtualBidTester"""
        self._virtual_bid_tester = virtual_bid_tester


class FunctionCodesMixin(object):
    """un lettore di informazioni che ha bisogno di tradurre il codice funzione
    del sottocampo $4"""

    def __init__(self, function_codes):
        """:function_codes: base.FunctionCodes"""
        self._function_codes = function_codes

    def _convert_function_code(self, code):
        code = self._function_codes[code]
        code = code[0].lower() + code[1:]
        return code
