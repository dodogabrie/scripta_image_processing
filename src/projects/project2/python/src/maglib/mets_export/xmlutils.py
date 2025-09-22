from lxml import etree

# metto i namespace in un dizionario
# questo dizionario viene usato da lxml per gestire i namespace
# i namespace vanno indicato con la sintassi {url_namespace}nome_elemento
# quando si crea un elemento
NAMESPACES = {
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    "xsd": "http://www.w3.org/2001/XMLSchema",
    "xlink": "http://www.w3.org/1999/xlink",
    "mets": "http://www.loc.gov/METS/",
    "metsrights": "http://cosimo.stanford.edu/sdr/metsrights/",
    "rd": "http://cosimo.stanford.edu/sdr/metsrights/",
    # 'dc'   : 'http://purl.org/dc/elements/1.1/',
    "mix": "http://www.loc.gov/mix/",
    "mods": "http://www.loc.gov/mods/v3",
    "audioMD": "http://www.loc.gov/audioMD/",
    "videoMD": "http://www.loc.gov/videoMD/",
}


class XmlUtils:
    @classmethod
    def find_or_create_element(
        cls, element_name, parent, *, namespace="mets", after=None, attributes=None
    ):
        """Cerca in parent un elemento con tag element_name (e namespace
        namespace) e lo ritorna, oppure, se non lo trova, lo crea come
        primo figli di parent e lo ritorna se il parametro after viene
        passato, nel caso che questo metodo debba creare un elemento,
        lo inserirà dopo l'elemento after (passato comprensivo di
        namespace)

        """
        attributes = attributes or {}
        element_fullname = cls.ns(element_name, namespace)
        element = cls._find_element(element_fullname, parent, attributes)
        if element is not None:
            return element

        element = etree.Element(element_fullname)

        for attr, value in attributes.items():
            element.attrib[attr] = value

        # se parent non ha figli, posso inserire in 0+1
        if after is None or (len(parent) == 0):
            el_index = 0
        else:
            for el_index, el in enumerate(parent):
                if el.tag == after:
                    el_index += 1  # inserisco dopo l'elemento after
                    break
        parent.insert(el_index, element)

        return element

    @classmethod
    def create_element(cls, tag, namespace="mets"):
        return etree.Element(cls.ns(tag, namespace), nsmap=NAMESPACES)

    @classmethod
    def element_with_text(cls, tag, namespace, text):
        el = cls.create_element(tag, namespace)
        el.text = text
        return el

    @classmethod
    def _find_element(cls, fullname, parent, attributes=None):
        attributes = attributes or {}
        for child in parent:
            if child.tag == fullname and cls._attrs_match(child, attributes):
                return child
        return None

    @classmethod
    def _attrs_match(cls, element, attributes):
        for attr, value in attributes.items():
            if element.attrib.get(attr) != value:
                return False
        return True

    @classmethod
    def get_namespace_tag(cls, tag, namespace="mets"):
        """
        dato il nome base di un tag ritorna il nome del tag incluso del
        namespace, se indicato.
        I namespace vanno passati a questo metodo con il prefisso.
        """
        # siccome lxml desidera gestirli con l'url, vengono convertiti col
        # dizionario NAMESPACES
        if not namespace:
            return tag
        else:
            return "{%s}%s" % (NAMESPACES[namespace], tag)

    @classmethod
    def xpath(cls, element, expression):
        return element.xpath(expression, namespaces=NAMESPACES)

    ns = get_namespace_tag
