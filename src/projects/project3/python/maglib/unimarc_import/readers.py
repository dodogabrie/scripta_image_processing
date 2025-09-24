# -*- coding: utf-8 -*-

import re

from maglib.unimarc_import.base_readers import (
    BidReferenceIRMixin,
    FunctionCodesMixin,
    InfoReader,
    InfoReadException,
    MultiSubFieldsFallbackIR,
    MultiSubFieldsIR,
    ParentRelationIRMixin,
    TitleReaderMixin,
)


class Type(InfoReader):
    info_name = "type"
    _TYPE_MAP = {
        "a": "testo a stampa",
        "b": "manoscritto",
        "c": "musica a stampa",
        "d": "musica manoscritta",
        "e": "cartografia a stampa",
        "f": "cartografia manoscritta",
        "g": "materiale video",
        "i": "registrazione sonora non musicale",
        "j": "registrazione sonora musicale",
        "k": "materiale grafico",
        "l": "risorsa elettronica",
        "m": "materiale multimediale",
        "r": "oggetto a tre dimensioni",
    }

    def read(self, marc_record):
        type_letter = marc_record.leader[6]
        try:
            tYpe = self._TYPE_MAP[type_letter]
        except KeyError:
            raise InfoReadException("Unknown type char %s" % type_letter)
        return [tYpe]


class BibLevel(InfoReader):
    info_name = "level"

    def read(self, marc_record):
        lvl = marc_record.leader[7]
        if lvl not in ("a", "m", "s", "c"):
            raise InfoReadException("Unknown level char %s" % lvl)
        return [lvl]


class Identifier(InfoReader):
    info_name = "identifier"

    def read(self, marc_record):
        v = self._decode_string(marc_record["001"].value())
        # TODO: verificare
        # pymarc rimuove '\' dal valore, per questo è necessario questo:
        v = v.replace(" ", "\\")
        return [v]


class Date100(InfoReader):
    """legge la data da 100"""

    info_name = "date"

    def read(self, marc_record):
        field = marc_record["100"]
        if not field:
            return []
        value = field.value()
        date_1 = value[9:13].strip()
        date_2 = value[13:17].strip()
        if date_1 == "----":
            date_1 = ""
        if date_2 == "----":
            date_2 = ""
        res = []
        if date_1:
            res.append(date_1)
        if date_2 and date_1 != date_2:
            res.append(date_2)
        return res


class Date210d(MultiSubFieldsIR):
    """legge la data da 210d, se non è presente in 100"""

    def __init__(self):
        super(Date210d, self).__init__("date", "210", ("d",))
        self._date100_reader = Date100()

    def read(self, marc_record):
        date100_readed = self._date100_reader.read(marc_record)
        if date100_readed:
            return []
        readed = super(Date210d, self).read(marc_record)
        if not readed:
            return []
        m = re.search(r"\d{4}((-\d{2})?(-\d{2})?)?", readed[0])
        if m:
            return [m.group(0)]
        m = re.search(r"\d\d\.\.", readed[0])
        if m:
            n = int(m.group(0)[:2])
            return [str(n) + "01", str(n + 1) + "00"]
        return []


class Language(InfoReader):
    """legge language da 101, normalizzando il valore"""

    info_name = "language"
    _language_map = {"it": "ita", "abs": None}

    def read(self, marc_record):
        if not marc_record["101"]:
            return []
        readed = []
        for sf in marc_record["101"].get_subfields("a"):
            v = sf.lower().strip()
            if v:
                v = self._language_map.get(v, v)
                readed.append(v)
        return readed


class Title(TitleReaderMixin, MultiSubFieldsIR):
    def __init__(self):
        super(Title, self).__init__(
            "title", "200", ("a", "c"), separator=" . ", strip_sf_spaces=True
        )

    def read(self, marc_record):
        readed = super(Title, self).read(marc_record)
        if marc_record["200"]:
            f200e = self._read_subfield(marc_record["200"], "f")
            if f200e:
                if readed:
                    readed[0] = " : ".join((readed[0], f200e))
                else:
                    readed = [f200e]
        return readed

    def _read_subfield(self, field, subfield_n):
        if subfield_n != "a":
            return super(Title, self)._read_subfield(field, subfield_n)

        sf_a = field.get_subfields("a")
        sf_a = [sf.strip() for sf in sf_a]
        sf_a = filter(None, sf_a)
        return " ; ".join(sf_a)


class TitleFull(TitleReaderMixin, MultiSubFieldsIR):
    """questo titolo cattura più campi"""

    def __init__(self):
        super(TitleFull, self).__init__(
            "title", "200", ("a", "c"), separator=" . ", strip_sf_spaces=True
        )

    @classmethod
    def _add_maybe_with_prefix(cls, s, added, prefix):
        if not s:
            return added
        return "%s%s%s" % (s, prefix, added)

    def read(self, marc_record):
        readed = super(TitleFull, self).read(marc_record)
        field = marc_record["200"]
        if not field:
            return readed
        if not readed:
            readed = [""]
        v = readed[0]
        for d in self._read_subfields(field, "d"):
            v = self._add_maybe_with_prefix(v, d, " = ")
        for e in self._read_subfields(field, "e"):
            v = self._add_maybe_with_prefix(v, e, " : ")
        for f in self._read_subfields(field, "f"):
            v = self._add_maybe_with_prefix(v, f, " / ")
        for g in self._read_subfields(field, "g"):
            v = self._add_maybe_with_prefix(v, g, " ; ")

        if not v:
            return []
        return [v]


class BasePublisher(InfoReader):
    info_name = "publisher"

    def read(self, marc_record):
        raise NotImplementedError()

    def _read_subfields(self, field, sf_n):
        if not field:
            return []
        return filter(
            None, [self._decode_string(v).strip() for v in field.get_subfields(sf_n)]
        )

    def _read_subfields_aceg(self, field):
        # ritorna quattro stringhe, con i valori dei quattro sottocampi a c e g
        # i valori ripetuti in "e" e "g" sono eliminati
        # i valori di ciascun sottocampo sono ritornate in una stringa,
        # separati da ,
        sfs_a = self._read_subfields(field, "a")
        sfs_c = self._read_subfields(field, "c")
        sfs_e = [
            sf for sf in self._read_subfields(field, "e") if not sf in list(sfs_a) + list(sfs_c)
        ]
        sfs_g = [
            sf
            for sf in self._read_subfields(field, "g")
            if not sf in list(sfs_a) + list(sfs_c) + list(sfs_e)
        ]
        return tuple(", ".join(sfs) for sfs in (sfs_a, sfs_c, sfs_e, sfs_g))

    def _read_ac_couples(self, field):
        return self._read_subfields_couples(field, "a", "c")

    def _read_eg_couples(self, field, ac_couples):
        eg_couples = self._read_subfields_couples(field, "e", "g")

        def _substr_in_list(substr, l):
            for s in l:
                if s and substr in s:
                    return True
            return False

        a_values, c_values = zip(*ac_couples)
        c = 0
        while c < len(eg_couples):
            if eg_couples[c][0] and _substr_in_list(eg_couples[c][0], a_values):
                eg_couples[c][0] = None
            if eg_couples[c][1] and _substr_in_list(eg_couples[c][1], c_values):
                eg_couples[c][1] = None
            c += 1

        return eg_couples

    def _read_subfields_couples(self, field, subf_a, subf_b):
        # legge i valori di due sottocampi, ritornando una lista di coppie
        # dove ogni valore è accoppiato con il suo corrispettivo
        a_values = []
        b_values = []
        last_a = False
        for sf_name, sf_value in field:
            if sf_name == subf_a:
                if last_a:
                    b_values.append(None)
                    a_values.append(sf_value)
                else:
                    a_values.append(sf_value)
                last_a = not last_a
            elif sf_name == subf_b:
                if last_a:
                    b_values.append(sf_value)
                else:
                    a_values.append(None)
                    b_values.append(sf_value)
                last_a = not last_a
        if last_a:
            b_values.append(None)

        return map(list, zip(a_values, b_values))

    def _read_210d(self, marc_record):
        if not marc_record["210"] or not marc_record["210"]["d"]:
            return None
        v = self._decode_string(marc_record["210"]["d"]).strip()
        v = re.sub(u"[¢\\\\](.+?)!", r"[\1]", v)
        # rimuovo una parentesi chiusa finale non bilanciata
        # m = re.match(r'^([^\[]+)\]$', v)
        # if m:
        #     return m.group(1)
        # m = re.match(r'^([^\(]+)\)$', v)
        # if m:
        #     return m.group(1)
        return v

    def _use_210d(self, marc_record):
        # dice se leggere il campo 210d
        return self._210d_is_descriptive(marc_record)

    def _210d_is_descriptive(self, marc_record):
        # una parentesi finale non bilanciata è irrilevante
        # 17..] => 17.., descrittiva
        # 1691) => 1691,  numerica
        # [1867?], descrittiva
        if not marc_record["210"] or not marc_record["210"]["d"]:
            return False
        f210_d = marc_record["210"]["d"]
        if re.match(r"^\d+[\]\)]?$", f210_d.strip()):
            return False
        return True

    def _balance_part1_final_parenthesis(self, marc_record, part1):
        # aggiunge eventualmente alla prima parte letta da 210 (a,c)
        # la parentesi di chiusura che è in 210$d e che non sarà inclusa
        # se 210$d è non descrittivo
        if self._use_210d(marc_record):
            return part1
        if not marc_record["210"] or not marc_record["210"]["d"]:
            return part1
        m = re.match(r"^[^\[\(]+([\]\)])", marc_record["210"]["d"].strip())
        if m:
            part1 += m.group(1)
        return part1

    def _clean_value(self, v):
        v = re.sub(r"\\(.*?)!", r"[\1]", v)
        return v

    # def _fix_final_parenthesis(self, marc_record, value):
    #     # eventualmente aggiunge la parentesi alla fine del prefisso
    #     #f210_d = marc_record['210']['d']
    #     if f210_d:
    #         m = re.match(r'[^\[\(]+([\]\)])', f210_d.strip())
    #         if m:
    #             prefix += m.group(1)
    #     return prefix


class Format(MultiSubFieldsIR):
    def __init__(self, subfields=("a", "c", "d", "e")):
        super(Format, self).__init__("format", "215", subfields, "", " ; ")

    def _clean_value(self, v):
        v = super(Format, self)._clean_value(v)
        v = re.sub(r"\[(.*?)!", r"[\1]", v)
        v = re.sub(r"\\\\(.*?)!", r"[\1]", v)
        v = re.sub(r"\\(.*?)!", r"[\1]", v)
        v = re.sub(u"°(.*?)!", r"[\1]", v)
        return v


class Format2(Format):
    """separa in modo particolare la $a dal resto del campo"""

    def __init__(self):
        super(Format2, self).__init__(("a", "d", "e"))

    def _read_subfield(self, field, subfield_n):
        # aggiunge $c quando si legge $a
        readed = super(Format2, self)._read_subfield(field, subfield_n)
        if subfield_n == "a":
            if field["c"]:
                fc = self._clean_value(field["c"].strip())
                if fc:
                    readed = " : ".join(filter(None, (readed, fc)))
        return readed

    def _clean_value(self, value):
        value = super(Format2, self)._clean_value(value)
        value = re.sub(",(?! )", ", ", value)
        value = re.sub("  +", " ", value)
        return value


class Description300(InfoReader):
    """legge le description dal campo 300"""

    info_name = "description"

    def read(self, marc_record):
        values = [
            self._decode_string(field["a"])
            for field in marc_record.get_fields("300")
            if field["a"]
        ]
        values = [self._clean_value(v) for v in values]
        values = filter(self._filter_value, values)
        values = [re.sub(r"([^\.])([\.;])$", r"\1", v) for v in values]
        if not values:
            return []
        s = " ; ".join(values)
        return [self._clean_value(s)]

    def _filter_value(self, value):
        # dice quali 300$a usare per comporre la description
        return True

    def _clean_value(self, v):
        v = super(Description300, self)._clean_value(v)
        v = re.sub(u"°(.*?)!", r"[\1]", v)
        v = re.sub(r"\s{2,}", " ", v)
        return v


class Description317(MultiSubFieldsIR):
    """legge description dal campo 317 (possessore)"""

    info_name = "description"

    def __init__(self):
        super(Description317, self).__init__(
            None, "317", ("a",), "'possessore:' ", repeat=True
        )

    def _clean_value(self, v):
        v = super(Description317, self)._clean_value(v)
        v = re.sub(
            r"^'possessore:'\s*(Provenienza|Possessore):\s*[\.\*]*\s*",
            "'possessore:' ",
            v,
        )
        return re.sub(r"[\.,]*\s*$", "", v)


class RelationIR(TitleReaderMixin, BidReferenceIRMixin, InfoReader):
    """importa un campo di tipo relation, che ha un riferimento ad un bid esterno"""

    info_name = "relation"

    def __init__(self, field_n, prefix, virtual_bid_tester, repeat=False):
        BidReferenceIRMixin.__init__(self, virtual_bid_tester)
        InfoReader.__init__(self)
        self._field_n = field_n
        self._prefix = prefix
        self._repeat = repeat

    def read(self, marc_record):
        values = []
        fields = marc_record.get_fields(self._field_n)
        if not self._repeat and fields:
            fields = fields[0:]
        for field in fields:
            relation_value = self._get_relation_value(field)
            relation_bid = self._get_relation_bid(field)
            value = "%s%s" % (self._prefix, relation_value)
            if not self._virtual_bid_tester(relation_bid):
                value = "%s {%s}" % (value, relation_bid)
            values.append(self._clean_value(value))
        return values

    def _get_relation_value(self, field):
        if field["a"]:
            return self._decode_string(field["a"])
        return ""

    def _get_relation_bid(self, field):
        """ottiene il bid a cui si riferisce il campo"""
        return re.sub(r"^001", "", field["1"])


class RelationIR_ae(RelationIR):
    """importa un campo di tipo relation, prendendo i sottocampi a ed e"""

    def _get_relation_value(self, field):
        fields = [self._decode_string(s) for s in [field["a"], field["e"]] if s]
        return " : ".join(fields)


class RelationParentTitleIR(ParentRelationIRMixin, RelationIR):
    """questa relation non viene inserita quando l'opera è in più parti e quindi
    il campo è già stato usato per costruire il titolo"""

    def read(self, marc_record):
        if self._work_is_part(marc_record):
            parent_title_field = self._first_relation_field(marc_record)
            if (
                parent_title_field is not None
                and parent_title_field == marc_record[self._field_n]
            ):
                return []
        return RelationIR.read(self, marc_record)


class Relation423(RelationIR):
    def __init__(self, virtual_bid_tester):
        super(Relation423, self).__init__(
            "423", "'pubblicato con:' ", virtual_bid_tester, repeat=True
        )

    def _get_relation_bid(self, field):
        return field["3"]


class Relation463(ParentRelationIRMixin, InfoReader):
    def __init__(self, virtual_bid_tester):
        super(Relation463, self).__init__("relation")
        self._descending_rel_reader = RelationIR(
            "463", "'comprende:' ", virtual_bid_tester, repeat=True
        )
        self._ascending_rel_reader = RelationIR(
            "463", "'fa parte di:' ", virtual_bid_tester, repeat=True
        )

    def read(self, marc_record):
        rel_type = self._field_463_rel_type(marc_record)
        if rel_type == self.ASCENDING_RELATION:
            return self._ascending_rel_reader.read(marc_record)
        elif rel_type == self.DESCENDING_RELATION:
            return self._descending_rel_reader.read(marc_record)
        return []


class ResponsabilityReader(MultiSubFieldsFallbackIR):
    """lettori che legget le informazioni su di un soggetto
    responsabile dell'opera (700,701,702,710,711,712)"""

    def __init__(self, records_retriever, info_name, field_n):
        super(ResponsabilityReader, self).__init__(
            records_retriever,
            info_name,
            field_n,
            ("a", "b"),
            repeat=True,
            separator=" ",
        )

    def _read_field(self, field):
        self._test_subfield_d(field)

        readed = super(ResponsabilityReader, self)._read_field(field)
        qualifier = self._read_qualifier(field)
        date = self._read_date(field)
        if qualifier:
            if date:
                readed += " <%s>, %s" % (date, qualifier)
            else:
                readed += " <%s>" % qualifier
        elif date:
            readed += " <%s>" % date

        return self._clean_value(readed)

    def _read_qualifier(self, f):
        if f["c"]:
            return self._clean_qualifier(f["c"])
        return None

    def _read_date(self, f):
        if f["f"]:
            return self._clean_date(f["f"])
        return None

    def _clean_qualifier(self, s):
        s = self._decode_string(s.strip())
        s = s.replace("<", "").replace(">", "")
        return s
        # return re.sub(r'<(.*)>?', r'\1', s)

    _clean_date = _clean_qualifier

    def _clean_value(self, v):
        v = super(ResponsabilityReader, self)._clean_value(v)
        v = v.replace("#", " ")
        v = v.replace("_", " ")
        v = re.sub(" ,", ",", v)
        return v

    def _test_subfield_d(self, field):
        # il $d non ci dovrebbe dati essere perché non si sa come trasporlo
        if field["d"]:
            raise InfoReadException(
                "il campo %d ha $d, contattare l'iccu" % self._field_n
            )


class Creator700_701(ResponsabilityReader):
    def __init__(self, records_retriever, field_n):
        super(Creator700_701, self).__init__(records_retriever, "creator", field_n)


class Contributor702_712(FunctionCodesMixin, ResponsabilityReader):
    def __init__(self, records_retriever, function_codes, field_n):
        FunctionCodesMixin.__init__(self, function_codes)
        ResponsabilityReader.__init__(self, records_retriever, "contributor", field_n)

    def _read_qualifier(self, field):
        qual1 = ResponsabilityReader._read_qualifier(self, field)
        if field["4"]:
            qual2 = self._convert_function_code(field["4"])
        else:
            return qual1

        # if qual1 and qual1 != qual2:
        #     raise InfoReadException('$4 e $c sono discordanti in '
        #                             '%s, contattare l\'iccu' % self._field_n)
        return qual2


class Contributor702(Contributor702_712):
    def __init__(self, records_retriever, function_codes):
        super(Contributor702, self).__init__(records_retriever, function_codes, "702")


class Contributor712(Contributor702_712):
    def __init__(self, records_retriever, function_codes):
        super(Contributor712, self).__init__(records_retriever, function_codes, "712")

    def _read_field(self, field):
        if field["4"] in ("650", "610"):
            return None
        return super(Contributor712, self)._read_field(field)


class Creator710_711(ResponsabilityReader):
    def __init__(self, records_retriever, field_n):
        super(Creator710_711, self).__init__(records_retriever, "creator", field_n)

    def _test_subfield_d(self, field):
        pass

    def _read_data(self, field):
        return None


# TODO: valutare se questi sono ora sempre più validi:
class Contributor702_712New(FunctionCodesMixin, MultiSubFieldsFallbackIR):
    def __init__(self, records_retriever, function_codes, field_n):
        FunctionCodesMixin.__init__(self, function_codes)
        MultiSubFieldsFallbackIR.__init__(
            self, records_retriever, "contributor", field_n, (), repeat=True
        )

    def _read_field(self, field):
        if not self._filter_field(field):
            return None

        part1 = self._read_part1(field)
        part2 = self._read_part2(field)
        if part2:
            part2 = "<%s>" % part2
        part3 = self._read_part3(field)
        if part3:
            part3 = "[%s]" % part3

        parts = filter(None, [part1, part2, part3])

        if parts:
            return " ".join(parts)
        return None

    def _read_part1(self, field, separator=" "):
        sfa = self._read_subfield(field, "a")
        sfb = self._read_subfield(field, "b")
        parts = [self._clean_value(part) for part in filter(None, [sfa, sfb])]
        value = separator.join(parts)
        value = re.sub("  +", " ", value)
        value = re.sub(" ,", ",", value)
        value = re.sub(r"\s*,\s*$", "", value)

        return value

    def _read_part2(self, field, subfields=("c", "d", "f")):
        parts = []
        for sf in subfields:
            value = self._read_subfield(field, sf)
            if value:
                value = self._clean_value(value)
                parts.append(value)
        value = " ; ".join(parts)
        value = value.replace("<", "").replace(">", "")
        return value

    def _read_part3(self, field):
        sf4 = self._read_subfield(field, "4")
        if sf4:
            return self._convert_function_code(sf4)
        # sfc = self._read_subfield(field, 'c')
        # if sfc:
        #     return sfc.replace('<', '').replace('>', '').strip()

        return None

    def _filter_field(self, field):
        return True

    def _clean_value(self, v):
        v = super(Contributor702_712New, self)._clean_value(v)
        v = v.replace("#", " ")
        v = v.replace("_", " ")
        v = re.sub(" ,", ",", v)
        return v


class Contributor702New(Contributor702_712New):
    def __init__(self, records_retriever, function_codes):
        super(Contributor702New, self).__init__(
            records_retriever, function_codes, "702"
        )


class Contributor712New(Contributor702_712New):
    def __init__(self, records_retriever, function_codes):
        super(Contributor712New, self).__init__(
            records_retriever, function_codes, "712"
        )

    def _read_part1(self, field):
        return super(Contributor712New, self)._read_part1(field, ". ")
