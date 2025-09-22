# -*- coding: utf-8 -*-

from lxml import etree

from maglib.mag import (
    audio_elements,
    contlet_elements,
    image_elements,
    video_elements,
)
from maglib.utils.misc import iso8601_time
from maglib.xmlbase import (
    Attribute,
    Complex_element_instance,
    Element,
    Simple_element_instance,
)

from .core_elements import Dc_element_with_lang, File
from .mets_elements import Mets


class Metadigit(Complex_element_instance):
    def __init__(self, xml_file=None):
        """:xml_file: se diverso da None, il file xml da caricare in questo
        oggetto Metadigit"""
        SCHEMA_LOCATION = "http://www.iccu.sbn.it/metaAG1.pdf metadigit.xsd"

        attributes = (
            Attribute("version"),
            Attribute("schemaLocation", "xsi"),
            Attribute("targetNamespace", "xsi"),
            Attribute("elementFormDefault"),
            Attribute("attributeFormDefault"),
        )

        elements = (
            Element(Gen, "gen"),
            Element(Bib, "bib"),
            Element(Stru, "stru", max_occurrences=None),
            Element(image_elements.Img, "img", max_occurrences=None),
            Element(audio_elements.Audio, "audio", max_occurrences=None),
            Element(video_elements.Video, "video", max_occurrences=None),
            Element(Ocr, "ocr", max_occurrences=None),
            Element(Doc, "doc", max_occurrences=None),
            Element(Dis, "dis", max_occurrences=None),
            Element(contlet_elements.Contlet, "sem", max_occurrences=None),
            Element(Extra, "extra"),
        )

        super(Metadigit, self).__init__(
            name="metadigit", attrs=attributes, sub_elements=elements
        )

        self.schemaLocation.value = SCHEMA_LOCATION

        if xml_file:
            self.build_from_xml_file(xml_file)

    def write(self, output, update_time=True, *args, **kwargs):
        """salva su un file l'xml che rappresenta Metadigit
        se update_time è vero, prima di scrivere il mag, viene aggiornato il
        tempo di ultima modifica, e se non presente quello di creazione"""
        if update_time:
            self._update_time()
        super(Metadigit, self).write(output, *args, **kwargs)

    def to_string(self, update_time=False, *args, **kwargs):
        """ritorna l'xml che rappresenta Metadigit come stringa
        se update_time è vero, prima di scrivere il mag, viene aggiornato il
        tempo di ultima modifica, e se non presente quello di creazione"""
        if update_time:
            self._update_time()
        return super(Metadigit, self).to_string(*args, **kwargs)

    def to_bytes(self, update_time=False, *args, **kwargs):
        if update_time:
            self._update_time()
        return super(Metadigit, self).to_bytes(*args, **kwargs)

    def as_xml(self, default_ns=True):
        if self.extra:
            metadigit = self.copy()  # remove extra from a copy
            extra_instance = metadigit.extra.pop(0)
            extra_comment_node = ExtraCommentSerde.serialize(extra_instance)
            el = metadigit.as_xml(default_ns)
            el.append(extra_comment_node)
            return el
        else:
            return super(Metadigit, self).as_xml(default_ns)

    def _update_time(self):
        if not self.gen:
            self.gen.add_instance()
        if not self.gen[0].creation.value:
            self.gen[0].creation.value = iso8601_time()
        self.gen[0].last_update.value = iso8601_time()

    @classmethod
    def from_xml_string(cls, xml_string):
        """Costruisce l'oggetto metadigit da una stringa xml"""

        metadigit = Metadigit()
        metadigit.build_from_xml_string(xml_string)
        return metadigit

    def build_from_xml(self, xml_node):
        super(Metadigit, self).build_from_xml(xml_node)
        extra_inst = ExtraCommentSerde.deserialize(xml_node)

        if extra_inst is not None:
            self.extra.append(extra_inst)

    def validate(self):
        """Effettua la validazione del mag nei confronti dello schema"""
        # TODO:
        raise NotImplementedError()


class ExtraCommentSerde(object):
    """Serialize/deserialize <extra> in an lxml comment node """

    PREFIX = "##mag <extra> element; do not edit##\n"

    @classmethod
    def serialize(cls, extra_instance):
        extra_string = extra_instance.to_string()
        return etree.Comment(cls.PREFIX + extra_string)

    @classmethod
    def deserialize(cls, xml_node):
        # xml_node is <metadigit>
        for element in xml_node.iter(tag=etree.Comment):
            if element.text.startswith(cls.PREFIX):
                xml_string = element.text[len(cls.PREFIX) :]
                return cls._load_from_xml_string(xml_string)

    @classmethod
    def _load_from_xml_string(cls, xml_string):
        extra = Extra(name="extra")
        extra.build_from_xml_string(xml_string)
        return extra


class Gen(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        attributes = (Attribute(name="creation"), Attribute(name="last_update"))
        elements = (
            Element(name="stprog"),
            Element(name="collection"),
            Element(name="agency"),
            Element(name="access_rights"),
            Element(name="completeness"),
            Element(image_elements.Img_group, "img_group", max_occurrences=None),
            Element(
                audio_elements.Audio_group, name="audio_group", max_occurrences=None
            ),
            Element(
                video_elements.Video_group, name="video_group", max_occurrences=None
            ),
        )
        super(Gen, self).__init__(
            sub_elements=elements, attrs=attributes, *args, **kwargs
        )


class Bib(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        attributes = (Attribute("level"),)
        elements = (
            Element(name="identifier", namespace="dc", max_occurrences=None),
            Element(Dc_element_with_lang, "title", "dc", max_occurrences=None),
            Element(name="creator", namespace="dc", max_occurrences=None),
            Element(name="publisher", namespace="dc", max_occurrences=None),
            Element(Dc_element_with_lang, "subject", "dc", max_occurrences=None),
            Element(Dc_element_with_lang, "description", "dc", max_occurrences=None),
            Element(name="contributor", namespace="dc", max_occurrences=None),
            Element(name="date", namespace="dc", max_occurrences=None),
            Element(Dc_element_with_lang, "type", "dc", max_occurrences=None),
            Element(Dc_element_with_lang, "format", "dc", max_occurrences=None),
            Element(Dc_element_with_lang, "source", "dc", max_occurrences=None),
            Element(name="language", namespace="dc", max_occurrences=None),
            Element(name="relation", namespace="dc", max_occurrences=None),
            Element(name="coverage", namespace="dc", max_occurrences=None),
            Element(name="rights", namespace="dc", max_occurrences=None),
            Element(Holdings, "holdings", max_occurrences=None),
            Element(Local_bib, "local_bib", max_occurrences=None),
            Element(Piece, "piece"),
        )

        super(Bib, self).__init__(
            sub_elements=elements, attrs=attributes, *args, **kwargs
        )


class Stru(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        # gli attributi sono tutti deprecati:
        attributes = (
            Attribute(name="descr"),
            Attribute(name="start"),
            Attribute(name="stop"),
        )

        elements = (
            Element(name="sequence_number"),
            Element(name="nomenclature"),
            Element(Stru_element, "element", max_occurrences=None),
            Element(Stru, "stru", max_occurrences=None),
        )

        super(Stru, self).__init__(
            sub_elements=elements, attrs=attributes, *args, **kwargs
        )


class Ocr(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        attributes = (Attribute(name="holdingsID"),)
        elements = (
            Element(name="sequence_number"),
            Element(name="nomenclature"),
            Element(name="usage", max_occurrences=None),
            Element(File, "file"),
            Element(name="md5"),
            Element(File, "source"),
            Element(name="filesize"),
            Element(image_elements.Format, "format"),
            Element(name="software_ocr"),
            Element(name="datetimecreated"),
            Element(name="note"),
        )

        super(Ocr, self).__init__(
            sub_elements=elements, attrs=attributes, *args, **kwargs
        )


class Doc(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        attributes = (Attribute(name="holdingsID"),)
        elements = (
            Element(name="sequence_number"),
            Element(name="nomenclature"),
            Element(name="usage", max_occurrences=None),
            Element(File, "file"),
            Element(name="md5"),
            Element(name="filesize"),
            Element(image_elements.Format, "format"),
            Element(name="datetimecreated"),
            Element(name="note"),
        )

        super(Doc, self).__init__(
            sub_elements=elements, attrs=attributes, *args, **kwargs
        )


class Dis(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        elements = (Element(Dis_item, "dis_item", max_occurrences=None),)
        super(Dis, self).__init__(sub_elements=elements, *args, **kwargs)


class Dis_item(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        elements = (
            Element(name="preview"),
            Element(name="available"),
            Element(File, "file"),
        )
        super(Dis_item, self).__init__(sub_elements=elements, *args, **kwargs)


class Holdings(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        attributes = (Attribute(name="ID"),)
        elements = (
            Element(name="library"),
            Element(name="inventory_number"),
            Element(Shelfmark, name="shelfmark", max_occurrences=None),
        )
        super(Holdings, self).__init__(
            sub_elements=elements, attrs=attributes, *args, **kwargs
        )


class Shelfmark(Simple_element_instance):
    def __init__(self, *args, **kwargs):
        super(Shelfmark, self).__init__(
            attrs=(Attribute(name="type"),), *args, **kwargs
        )


class Local_bib(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        elements = (
            Element(name="geo_coord", max_occurrences=None),
            Element(name="not_date", max_occurrences=None),
        )
        super(Local_bib, self).__init__(sub_elements=elements, *args, **kwargs)


class Piece(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        elements = (
            Element(name="year"),
            Element(name="issue"),
            Element(name="stpiece_per"),
            Element(name="part_number"),
            Element(name="part_name"),
            Element(name="stpiece_vol"),
        )

        super(Piece, self).__init__(sub_elements=elements, *args, **kwargs)


class Stru_element(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        attributes = (Attribute(name="descr"), Attribute(name="num"))
        elements = (
            Element(name="nomenclature"),
            Element(File, "file"),
            Element(name="identifier", namespace="dc"),
            Element(Piece, "piece"),
            Element(name="resource"),
            Element(Stru_element_start_stop, "start"),
            Element(Stru_element_start_stop, "stop"),
        )

        super(Stru_element, self).__init__(
            sub_elements=elements, attrs=attributes, *args, **kwargs
        )


class Stru_element_start_stop(Simple_element_instance):
    def __init__(self, *args, **kwargs):
        attributes = (Attribute(name="sequence_number"), Attribute(name="offset"))
        super(Stru_element_start_stop, self).__init__(attrs=attributes, *args, **kwargs)


class Extra(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        super(Extra, self).__init__(
            sub_elements=(Element(Mets, name="mets", namespace="mets"),),
            *args,
            **kwargs
        )
