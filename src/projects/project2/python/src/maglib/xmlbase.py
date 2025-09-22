# -*- coding: utf-8 -*-

import copy
import io

from lxml import etree

# il namespace deve essere dato per esteso e non con il prefisso alla
# libreria lxml, quando si serializza un xml.
# Grazie a questa mappatura si possono passare namespace con prefisso e
# verranno serializzati correttamente
NAMESPACES = {
    "dc": "http://purl.org/dc/elements/1.1/",
    "niso": "http://www.niso.org/pdfs/DataDict.pdf",
    "xlink": "http://www.w3.org/1999/xlink",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    "xml": "http://www.w3.org/XML/1998/namespace",
    "mag": "http://www.iccu.sbn.it/metaAG1.pdf",
    # mets namespaces
    "mets": "http://www.loc.gov/METS/",
    "mods": "http://www.loc.gov/mods/v3",
    "metsrights": "http://cosimo.stanford.edu/sdr/metsrights/",
    "mix": "http://www.loc.gov/mix/",
    "audioMD": "http://www.loc.gov/audioMD/",
}

# mappa dei namespace in cui quello mag è quello locale e quindi non
# scritto esplicitamente nel xml serializzato
NAMESPACES_WITH_DEF = NAMESPACES.copy()
NAMESPACES_WITH_DEF[None] = NAMESPACES_WITH_DEF.pop("mag")

# this is used when parsing to detect namespace prefix
NAMESPACES_WITH_DEF_URI_TO_PREFIX = {
    uri: prefix for prefix, uri in NAMESPACES_WITH_DEF.items()
}
# allow to migrate from xlink with wrong namespace previously used in mag
NAMESPACES_WITH_DEF_URI_TO_PREFIX["http://www.w3.org/TR/xlink"] = "xlink"


class Base_xml_entity(object):
    """Classe astratta per fattorizzare le classi di attributi o elementi xml.
    Implementa il costruttore e la gestione automatica o meno della
    visibilità."""

    def __init__(self, name="", namespace=None, value=None, visible=None):
        """
        name e namespace sono il nome e il namespace del nodo
        value è il valore se si tratta di attributo, o il testo se si tratta di un elemento
        Attrs viene comunque impostato perchè viene usato da __getattr__"""
        # il namespace locale deve essere passato con chiave None a lxml
        # un oggetto che non esprime namespace, e quindi appartiene al namespace locale,
        # deve quind avere come valore di namespace esattamente None

        self._name = name
        self._namespace = namespace
        self._value = value
        self._visible = None

        if visible is not None:
            self.visible = visible

    @property
    def visible(self):
        """se visible è stato impostato manualmente, verrà ritornato il suo valore
        Altrimenti visible viene calcolato dinamicamente in base alla
        presenza o meno di un valore nell'elemento"""
        if self._visible is None:
            return self._get_visibility()
        return self._visible

    @visible.setter
    def visible(self, visible):
        self._visible = bool(visible)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        if new_value is not None:
            if not isinstance(new_value, str):
                raise TypeError("use only string for element values")
        self._value = new_value

    def _get_visibility(self):
        """dice se l'elemento deve essere aggiunto all'xml, in base al fatto se
        contiene o no dati"""
        return self.value != None

    def get_full_name(self):
        """ritorna il nome come stringa, considerando la presenza
        del namespace"""
        # il namespace di default è mag, sia che dopo venga reso esplicito o no
        # nella serializzazione
        ns_prefix = NAMESPACES_WITH_DEF[self._namespace]
        return "{%s}%s" % (ns_prefix, self.get_simple_name())

    def get_simple_name(self):
        """ritorna il nome senza namespace"""
        return self._name

    def copy(self):
        """ritorna una copia indipendente dell'oggetto"""
        return copy.deepcopy(self)

    def _convert_full_name(self, tag_name):
        """tag_name: stringa
        Ritorna il nome del tag, considerando il namespace;
        se il tag appartiene ad un namespace, ritorna
           (namespace, nome senza namespace),
        altrimenti ritorna (None, nome)"""
        if tag_name.startswith("{"):
            closing_brace = tag_name.find("}")
            namespace = tag_name[1:closing_brace]
            # il ns 'mag' va comunque tenuto come None all'interno degli
            # oggetti come il ns locale, quindi uso NAMESPACES_WITH_DEF
            try:
                namespace_prefix = NAMESPACES_WITH_DEF_URI_TO_PREFIX[namespace]
            except KeyError:
                raise Exception("Namespace {} non conosciuto".format(namespace))
            simple_name = tag_name[closing_brace + 1 :]
        else:
            namespace_prefix = None
            simple_name = tag_name

        return (namespace_prefix, simple_name)


class Attribute(Base_xml_entity):
    """Rappresenta un attributo dell'xml"""

    def get_full_name(self):
        # nel mag gli attributi sono di default non qualificati, quindi se il namespace
        # è vuoto non devo intendere il namespace di default, ma nessun namespace
        if self._namespace is None:
            return self.get_simple_name()
        return super(Attribute, self).get_full_name()


class Simple_element_instance(Base_xml_entity):
    """Rappresenta una singola istanza di un elemento semplice, senza sottonodi
    Gli elementi veri e propri (Simple_element) sono una lista di queste
    istanze, per permettere ad un elemento di apparire più volte."""

    # set default attribute values for the element
    # those defaults will be applied when converting the instance to xml element
    # if an attribute for the value is not present
    DEFAULT_ATTRIBUTES = {}

    def __init__(self, attrs=(), *args, **kwargs):
        """attrs è la lista di attributi validi per l'elemento, lista di
        oggetti Attribute"""
        super(Simple_element_instance, self).__init__(*args, **kwargs)
        self._attributes = self._init_attributes(attrs)

    def as_xml(self, default_ns=True):
        """ritorna l'elemento xml che questo oggetto rappresenta
        :default_ns: usa per gli elementi mag il namespace di default,
        senza prefisso"""
        nsmap = NAMESPACES_WITH_DEF if default_ns else NAMESPACES
        element = etree.Element(self.get_full_name(), nsmap=nsmap)

        if self.value:
            element.text = self.value
        for attr_name in self._attributes:
            attribute = getattr(self, attr_name)
            if attribute.visible:
                element.attrib[attribute.get_full_name()] = attribute.value

        self._set_attribute_defaults(element)
        return element

    def build_from_xml(self, xml_node):
        """riempe l'oggetto con le informazioni presenti nel nodo element tree xml_node"""
        # se il testo è None viene impostato a '' in modo che poi il nodo sia
        # visibile quando serializzato
        self.value = xml_node.text or ""
        self._add_attributes(xml_node.attrib)

    def write(
        self,
        output,
        pretty_print=True,
        encoding="utf-8",
        default_ns=True,
        xml_declaration=True,
    ):
        """serializza l'elemento come stringa xml
        :output: può essere un path oppure un file handle
        :pretty_print:, se vero, formatta l'xml con tab e a capo
        :default_ns: usa per gli elementi mag il namespace di default,
        senza prefisso
        :xml_declaration:, se vero, aggiunge la line di intestazione xml"""

        if isinstance(output, io.TextIOBase):
            raise ValueError("do not use textual streams with write()")

        tree = self._get_xml_tree(default_ns)
        tree.write(
            output,
            pretty_print=pretty_print,
            encoding=encoding,
            xml_declaration=xml_declaration,
        )

    def to_bytes(
        self,
        pretty_print=False,
        encoding="utf-8",
        default_ns=True,
        xml_declaration=True,
    ):
        """ritorna l'elemento xml serializzato come stringa"""

        tree = self._get_xml_tree(default_ns)
        return etree.tostring(
            tree,
            pretty_print=pretty_print,
            encoding=encoding,
            xml_declaration=xml_declaration,
        )

    def to_string(self, pretty_print=False, default_ns=True):
        tree = self._get_xml_tree(default_ns)

        return etree.tostring(
            tree, pretty_print=pretty_print, encoding="unicode", xml_declaration=False
        )

    def _get_xml_tree(self, default_ns):
        element = self.as_xml(default_ns=default_ns)
        tree = etree.ElementTree(element)
        etree.cleanup_namespaces(tree)
        return tree

    def _init_attributes(self, attrs_list):
        """imposta gli attributi, ogni oggetto Attribute passato viene inserito come variabile
        dell'oggetto, con lo stesso nome dell'attributo"""
        _attributes = []  # l'elenco dei nomi degli attributi
        for attr in attrs_list:
            attr_name = attr.get_simple_name()
            setattr(self, attr_name, attr)
            # tengo l'elenco dei nomi degli attributi per scorrerli
            _attributes.append(attr_name)
        return tuple(_attributes)

    def _get_visibility(self):
        """per essere visibile questo oggetto deve avere un valore oppure
        degli attributi con valore"""
        if self.value != None:
            return True
        for attr_name in self._attributes:
            attribute = getattr(self, attr_name)
            if attribute.visible:
                return True
        return False

    def _add_attributes(self, xml_attributes):
        """aggiunge gli attributi espressi dal dizionario xml_attributes all'oggetto, se essi
        sono attributi validi per l'oggetto. Da notare che in etree il dizionario con gli
        attributi di un nodo xml è ottenibile dalla variabile attrib. xml_node.attrib"""
        for attr_fullname, attr_value in xml_attributes.items():
            attr_namespace, attr_name = self._convert_full_name(attr_fullname)
            if self._test_attribute_presence(attr_name, attr_namespace):
                attribute = getattr(self, attr_name)
                attribute.value = attr_value
            else:
                raise ValueError(
                    "Errore maglib: impossibile inserire l'attributo %s nell'elemento %s"
                    % (attr_fullname, self._name)
                )

    def _test_attribute_presence(self, attr_name, attr_namespace):
        """controlla se un attributo va bene per questo oggetto"""

        if attr_name not in self._attributes:
            return False
        else:
            # controllo l'uguaglianza del namespace, nell'oggetto il namespace
            # è salvato come prefisso e lo converto in forma estesa
            return getattr(self, attr_name)._namespace == attr_namespace

    @classmethod
    def _set_attribute_defaults(cls, element):
        for attr, value in cls.DEFAULT_ATTRIBUTES.items():
            if attr not in element.attrib:
                element.attrib[attr] = value


class Complex_element_instance(Simple_element_instance):
    """
    Rappresenta una singola istanza di un nodo xml che può contenere altri elementi.
    Gli elementi veri e propri (Complex_element) sono una lista di queste istanze.
    Questa classe si appoggia a 3 variabili (_objectAttributes, _simpleElements, _complexElements)
    per elencare i vari tipi di contenuto del nodo, che andranno ciascuno nella variabile con
    lo stesso nome
    _attributes sono gli attributi del nodo (classe Attribute)
    _simple_elements sono i sotto-elementi semplici, senza sottonodi  (classe Simple_element)
    _complex_elements contiene i sotto-elementi complessi del nodo (classe Complex_element)
    """

    # l'attributo value (cioè il testo del nodo xml) è supportato da questa classe ma in realtà
    # non dovrebbe essere usato, visto che solitamente un nodo xml ha o testo o sottoelementi

    def __init__(self, sub_elements=(), elements_order=None, *args, **kwargs):
        """sub_elements: gli elementi compresi in questo oggetto
        elements_order: lista che indica il nome degli elementi nell'ordine in cui devono
        essere inseriti. Se non data, verrà usato l'ordine in cui sono passati nel costruttore"""
        super(Complex_element_instance, self).__init__(*args, **kwargs)

        self._sub_elements = self._init_elements(sub_elements)

        # se non presente imposto l'ordine di default dei sottoelementi
        if elements_order:
            self._sub_elements_order = elements_order
        else:
            self._sub_elements_order = self._sub_elements

    def as_xml(self, default_ns=True):
        xml_element = super(Complex_element_instance, self).as_xml(default_ns)
        # il genitore costruisce l'elemento base,
        # mancano da aggiungere i sottoelementi
        for sub_element_name in self._sub_elements_order:
            sub_element = getattr(self, sub_element_name)
            for instance in sub_element:
                if instance.visible:
                    sub_element_xml = instance.as_xml()
                    xml_element.append(sub_element_xml)
        return xml_element

    def build_from_xml(self, xml_node):
        """riempe l'oggetto vuoto con le informazioni presenti in un nodo xml element tree"""
        # il genitore importa valore test e attributi. il testo non dovrebbe essere
        # presente, vedi sopra
        super(Complex_element_instance, self).build_from_xml(xml_node)

        for element_node in xml_node:
            if element_node.tag is etree.Comment:
                continue
            element_namespace, element_name = self._convert_full_name(element_node.tag)
            if self._test_subelement_presence(element_name, element_namespace):
                element_object = getattr(self, element_name)
                element_instance = element_object.add_instance()
                element_instance.build_from_xml(element_node)
            else:
                raise Exception(
                    "Impossibile inserire l'elemento %s nell'elemento %s"
                    % (element_node.tag, self.get_full_name())
                )

    def build_from_xml_string(self, xml_string):
        parser = etree.XMLParser(remove_blank_text=True)
        xml_node = etree.fromstring(xml_string, parser=parser)
        self.build_from_xml(xml_node)

    def build_from_xml_file(self, fiLe, remove_blank_text=True):
        parser = etree.XMLParser(remove_blank_text=remove_blank_text)
        xml_tree = etree.parse(fiLe, parser)
        xml_node = xml_tree.getroot()
        self.build_from_xml(xml_node)

    def _init_elements(self, elements_list):
        _elements = []
        for element in elements_list:
            setattr(self, element.name, element)
            _elements.append(
                element.name
            )  # i nomi degli elementi sono salvati in una lista in
            # modo da poterli scorrere
        return tuple(_elements)

    def _get_visibility(self):
        """
        la visibilità dell'oggetto viene calcolata dinamicamente solo se la variabile
        self.visibility non è stata impostata
        Se non è impostata l'oggetto è visibile se ha attributi o sotto-elementi visibili
        """
        # il genitore controlla valore testo e attributi
        if super(Complex_element_instance, self)._get_visibility():
            return True
        # rimangono da controllare i sottoelementi
        for element_name in self._sub_elements:
            element = getattr(self, element_name)
            if element.visible:
                return True
        return False

    def _test_subelement_presence(self, element_name, element_namespace):
        """dice se un elemento può essere un sottoelemento valido di
        questo oggetto"""
        if not element_name in self._sub_elements:
            return False
        else:
            return getattr(self, element_name).namespace == element_namespace


class Element(object):
    u"""un elemento xml, ripetibile. Questa classe è composta in pratica da
    una lista di Simple_element_instance o di Complex_element_instance"""

    def __init__(
        self,
        instance_class=Simple_element_instance,
        name="",
        namespace=None,
        max_occurrences=1,
    ):
        """name: il nome di ciascuna istanza
        namespace: l'eventuale namespace di ciascuna istanza
        instance_class: la classe usata per costruire le istanze contenute
        max_occurrences: il numero di istanze massime che si possono tenere, se
         None non c'è limite"""

        self.Instance = instance_class

        self.name = name
        self.namespace = namespace

        self._max_occurrences = max_occurrences

        self._instances = []

    @property
    def max_occurrences(self):
        return self._max_occurrences

    def __getattr__(self, attr_name):
        if attr_name == "visible":
            for instance in self._instances:
                if instance.visible:
                    return True
            return False
        return super(Element, self).__getattribute__(attr_name)

    # questi metodi permettono di trattare l'oggetto come una lista,
    # per accedere alle sue istanze
    def __iter__(self):
        return self._instances.__iter__()

    def __getitem__(self, index):
        return self._instances.__getitem__(index)

    def __len__(self):
        return len(self._instances)

    def __delitem__(self, index):
        return self._instances.__delitem__(index)

    def append(self, instance):
        return self._instances.append(instance)

    def insert(self, index, instance):
        return self._instances.insert(index, instance)

    def pop(self, index=0):
        return self._instances.pop(index)

    def remove(self, instance):
        return self._instances.remove(instance)

    def sort(self, *args, **kwargs):
        return self._instances.sort(*args, **kwargs)

    def add(self, position=-1):
        """aggiunge un'istanza all'oggetto, alla posizione n+1-sima, e
        poi la ritorna. Di default, e per position negativa, l\'elemento viene
        aggiunto comunque alla fine"""
        # controllo se c'è spazio per l'istanza
        if self._max_occurrences and len(self._instances) >= self._max_occurrences:
            raise RuntimeError(
                "Numero massimo di instanze raggiunto per "
                "l'elemento %s. Istanza non aggiunta" % self.Instance
            )

        if position < 0 or position > len(self._instances):
            position = len(self._instances)

        new_instance = self.Instance(name=self.name, namespace=self.namespace)

        self._instances.insert(position, new_instance)

        return self._instances[position]

    def add_instance(self, *args, **kwargs):
        """aggiunge un'istanza all'oggetto, alla posizione n+1-sima, e
        poi la ritorna. Di default, e per position negativa, l\'elemento viene
        aggiunto comunque alla fine
        DEPRECATO, usare add()"""
        return self.add(*args, **kwargs)

    def remove_instance(self, instance):
        """rimuove un'instanza dall'oggetto
        DEPRECATO, usare remove()"""
        return self._instances.remove(instance)

    def pop_instance(self, index=0):
        """riumove un'instanza dall'oggetto in base al suo indice
        DEPRECATO, usare pop()"""
        return self._instances.pop(index)

    def clear(self):
        """elimina tutte le istanze dell'elemento"""
        while self._instances:
            self._instances.pop()

    # Queste due funzioni sono delle scorciatoie per operare sugli Element
    # composti da al più una istanza di una istanza elemento semplice
    def set_value(self, new_value):
        """imposta il valore della prima istanza dell'oggetto.
        se new_value è None cancella la prima istanza.
        Funziona solo per gli Element formati da una sola
        Simple_element_instance"""
        if (
            not issubclass(self.Instance, Simple_element_instance)
            or self._max_occurrences != 1
        ):
            raise ValueError(
                "Usare set_value solo per gli Element formati da "
                "una sola Simple_element_instance"
            )
        if new_value is None:
            if self._instances:
                self.pop_instance()
        else:
            if not self._instances:
                self.add_instance()
            self._instances[0].value = new_value

    def get_value(self):
        """recupera il valore dalla prima istanza dell'oggetto.
        se non ci sono istanza, ritorna None
        Funziona solo per gli Element formati da una sola
        Simple_element_instance"""
        if (
            not issubclass(self.Instance, Simple_element_instance)
            or self._max_occurrences != 1
        ):
            raise ValueError(
                "Usare get_value solo per gli Element formati da "
                "una sola Simple_element_instance"
            )

        if not self._instances:
            return None
        return self._instances[0].value
