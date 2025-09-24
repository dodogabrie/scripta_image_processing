# -*- coding: utf-8 -*-

import logging
import os
import re
import time

from lxml import etree

from maglib.xmlbase import Element

logger = logging.getLogger(__name__)


def iso8601_time(datetime=None):
    """formatta la data ottenuta da una chiamata stat nel formato iso
    desiderato dal mag
    se datetime==None viene usata la data e l'ora corrente"""
    if not datetime:
        datetime = time.gmtime()
    else:
        datetime = time.gmtime(datetime)
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", datetime)


class MagResourcePathParseError(Exception):
    def __init__(self, path):
        self._path = path

    def __str__(self):
        return "%s is not a normal mag resource path" % self._path


class MagResourcePath(object):
    """legge il path di una risorsa come è scritto nel mag e permette di
    accedere alle sue componenti"""

    _path_regex = re.compile(
        r"^(?:\./)?([^/]+)/(?i)(tiff|jpeg\d*|thumbs|pdf)/"
        r"(([^/]+?_)?(\d+(?:[a-z]{1,2}\d*)?))\.(tif|jpg|pdf)$",
        re.VERBOSE,
    )

    def __init__(self, path):
        """:path: il path della risorsa per come è nel mag"""
        m = self._path_regex.match(path)
        if not m:
            raise MagResourcePathParseError(path)

        self._dotslash = path.startswith("./")
        self._mag_dirname = m.group(1)
        self._resource_dirname = m.group(2)
        self._file_basename = m.group(3)
        self._file_basename_no_prog_part = m.group(4)
        self._file_progressive_part = m.group(5)
        self._file_extension = m.group(6)

    @property
    def mag_dirname(self):
        """nome della directory del mag"""
        return self._mag_dirname

    @property
    def resource_dirname(self):
        """nome della directory del formato delle risorse"""
        return self._resource_dirname

    @property
    def file_basename(self):
        """nome base del file"""
        return self._file_basename

    @property
    def file_basename_no_prog_part(self):
        """nome base del file senza parte progressiva"""
        return self._file_basename_no_prog_part

    @property
    def file_progressive_part(self):
        """parte progressiva del nome del file"""
        return self._file_progressive_part

    @property
    def file_extension(self):
        """estensione del file"""
        return self._file_extension

    @property
    def dotslash(self):
        """dice se il path inizia con "./" o meno"""
        return self._dotslash

    @classmethod
    def get_dirnames(cls, fpath):
        """dato il path di un file, ritorna l'elenco di nomi di directory
        che lo compongono, a partire da quella di livello più profondo"""
        dirpath = os.path.dirname(fpath)
        dirpath = os.path.normpath(dirpath)
        if dirpath == os.path.curdir:
            return []
        dirnames = []
        head, tail = os.path.split(dirpath)
        while head or tail:
            dirnames.append(tail)
            if head == "/":
                break
            head, tail = os.path.split(head)
        return dirnames

    # nomi di directory che possono indicare il formato immagine di una risorsa
    known_img_format_dirs = (r"^tiff$", r"^jpe?g.*$", r"^png$", r"^thumb(nail)?s$")
    _compiled_known_img_format_dirs = [
        re.compile(reg, re.I) for reg in known_img_format_dirs
    ]

    @classmethod
    def guess_img_format_from_dirnames(cls, fpath):
        """individua il formato immagine (tiff, jpeg300,  ...) della risorsa
        dai nomi della directory che compongono il path della risorsa
        :param str fpath: path della risorsa
        :return: nome del formato o None
        :rtype: str"""
        return cls._match_dirnames(fpath, cls._compiled_known_img_format_dirs)

    # nomi di directory che possono indicare il formato di una risorsa
    # TODO: aggiungere a questa variabile nomi di formati non-immagine,
    # se servono a qualcuno che usa guess_format_from_dirnames
    known_format_dirs = known_img_format_dirs
    _compiled_known_format_dirs = [
        re.compile(reg, re.I) for reg in known_img_format_dirs
    ]

    @classmethod
    def guess_format_from_dirnames(cls, fpath):
        """individua il formato della risorsa in base ai componenti directory
        del path"""
        return cls._match_dirnames(fpath, cls._compiled_known_format_dirs)

    @classmethod
    def _match_dirnames(cls, fpath, regexes):
        # matcha il primo componente directory del path di una risorsa
        # in una lista di espressioni regolari. Parte dal livello più profondo
        # e torna il primo livello che matcha
        dirnames = cls.get_dirnames(fpath)
        for dirname in dirnames:
            for regex in regexes:
                if regex.match(dirname):
                    # il formato deve essere normalizzato in minuscolo ?
                    return dirname
                    # return dirname.lower()
        return None


class BibInfo(dict):
    """dizionario con le informazioni inseribili nella sezione <bib>"""

    dc_keys = (
        "identifier",
        "title",
        "creator",
        "publisher",
        "subject",
        "description",
        "contributor",
        "date",
        "type",
        "format",
        "source",
        "language",
        "relation",
        "coverage",
        "rights",
    )

    non_dc_keys = (
        "level",
        "inventory-number",
        "shelfmark",
        "library",
        "year",
        "issue",
        "stpiece_per",  # piece seriale
        "part_number",
        "part_name",
        "stpiece_vol",  # piece componente
    )
    keys = dc_keys + non_dc_keys

    def __setitem__(self, key, value):
        if key not in self.keys:
            raise ValueError("key %s unknown for bib info" % key)
        return super(BibInfo, self).__setitem__(key, value)

    def add_value(self, key, value):
        if key not in self:
            self[key] = []
        self[key].append(value)


class IdentifierReader(object):
    """strumenti per leggere il dc:identifier da un mag"""

    # TAG che mi interessano con namespace espanso:
    _bib_tag = "{http://www.iccu.sbn.it/metaAG1.pdf}bib"
    _dc_identifier_tag = "{http://purl.org/dc/elements/1.1/}identifier"

    @classmethod
    def from_xml_file(cls, fpath):
        """legge il dc:identifier da un MAG. ritorna None se non si riesce
        a leggere o il MAG non ha dc:identifier"""
        try:
            iterparser = etree.iterparse(fpath)
        except IOError:
            logger.warn("Impossibile aprire %s per ricavarne l'id", fpath)
            return None

        try:
            for action, el in iterparser:
                if action == "end" and el.tag == cls._bib_tag:
                    # <bib> finito, se c'era un identifier
                    # dovevo averlo già trovato !
                    return None
                if action == "end" and el.tag == cls._dc_identifier_tag:
                    # dc:identifier nel mag è anche in element, a me interessa
                    # solo se è figlio di <bib>
                    parent = el.getparent()
                    if parent.tag == cls._bib_tag:
                        logger.debug(
                            "letto dc:identifier %s dal mag %s", el.text, fpath
                        )
                        return el.text

            logger.debug("dc:identifier non trovato nel mag %s", fpath)
            return None
        except etree.XMLSyntaxError:
            logger.warn("Impossibile leggere l'xml %s per ricavarne l'id", fpath)
            return None


def ensure_mag_elements(mag_obj: Element, path: str) -> None:
    components = path.split(".")
    cur_node = mag_obj
    for component in components:
        elements = getattr(cur_node, component)
        if len(elements) == 0:
            elements.add_instance()
        cur_node = elements[0]
