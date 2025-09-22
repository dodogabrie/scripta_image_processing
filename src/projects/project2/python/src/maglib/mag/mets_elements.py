from maglib.xmlbase import (
    Attribute,
    Complex_element_instance,
    Element,
    Simple_element_instance,
)

MODS_IDENTIFIER_TYPES = (
    "subsis",
    "cont",
    "gest",
    "desc",
    "kardex",
)


class Mets(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        super(Mets, self).__init__(
            name="mets",
            namespace="mets",
            sub_elements=(
                Element(MetsHdr, name="metsHdr", namespace="mets"),
                Element(DmdSec, name="dmdSec", namespace="mets"),
                Element(AmdSec, name="amdSec", namespace="mets"),
            ),
        )


# MetsHdr elements
class MetsHdr(Complex_element_instance):
    visible = True

    def __init__(self, *args, **kwargs):
        super(MetsHdr, self).__init__(
            name="metsHdr",
            namespace="mets",
            sub_elements=(
                Element(Agent, name="agent", namespace="mets", max_occurrences=None),
            ),
        )


class Agent(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        super(Agent, self).__init__(
            name="agent",
            namespace="mets",
            attrs=(
                Attribute("ROLE"),
                Attribute("OTHERROLE"),
                Attribute("TYPE"),
                Attribute("OTHERTYPE"),
                Attribute("ID"),
            ),
            sub_elements=(Element(name="name", namespace="mets"),),
        )


# DmdSec elements
class DmdSec(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        super(DmdSec, self).__init__(
            name="dmdSec",
            namespace="mets",
            sub_elements=(Element(ModsMdWrap, name="mdWrap", namespace="mets"),),
        )


class BaseMdWrap(Complex_element_instance):
    @property
    def XmlData(self):
        raise NotImplementedError()

    def __init__(self, *args, **kwargs):
        super(BaseMdWrap, self).__init__(
            name="mdWrap",
            namespace="mets",
            attrs=(Attribute("MDTYPE"), Attribute("MIMETYPE"), Attribute("LABEL")),
            sub_elements=(Element(self.XmlData, name="xmlData", namespace="mets"),),
        )


class ModsXmlData(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        sub_elements = (Element(Mods, name="mods", namespace="mods"),)
        super(ModsXmlData, self).__init__(*args, **kwargs, sub_elements=sub_elements)


class ModsMdWrap(BaseMdWrap):
    XmlData = ModsXmlData


class Mods(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        super(Mods, self).__init__(
            name="mods",
            namespace="mods",
            sub_elements=(
                Element(
                    Identifier,
                    name="identifier",
                    namespace="mods",
                    max_occurrences=None,
                ),
            ),
        )


class Identifier(Simple_element_instance):
    def __init__(self, *args, **kwargs):
        super(Identifier, self).__init__(
            name="identifier", namespace="mods", attrs=(Attribute("type"),)
        )


# AmdSec elements
class AmdSec(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        super(AmdSec, self).__init__(
            name="amdSec",
            namespace="mets",
            sub_elements=(Element(RightsMd, name="rightsMD", namespace="mets"),),
        )


class RightsMd(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        super(RightsMd, self).__init__(
            name="rightsMD",
            namespace="mets",
            attrs=(Attribute("ID"),),
            sub_elements=(Element(RightsMdWrap, name="mdWrap", namespace="mets"),),
        )


class RightsXmlData(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        sub_elements = (
            Element(
                RightsDeclarationMD, name="RightsDeclarationMD", namespace="metsrights"
            ),
        )
        super(RightsXmlData, self).__init__(*args, **kwargs, sub_elements=sub_elements)


class RightsMdWrap(BaseMdWrap):
    DEFAULT_ATTRIBUTES = {"MIMETYPE": "text/xml", "MDTYPE": "METSRIGHTS"}
    XmlData = RightsXmlData


class RightsDeclarationMD(Complex_element_instance):
    DEFAULT_ATTRIBUTES = {"RIGHTSCATEGORY": "COPYRIGHTED"}

    def __init__(
        self, name="RightsDeclarationMD", namespace="metsrights", *args, **kwargs
    ):
        super(RightsDeclarationMD, self).__init__(
            name=name,
            namespace=namespace,
            attrs=(Attribute("RIGHTSCATEGORY"),),
            sub_elements=(
                Element(RightsHolder, name="RightsHolder", namespace="metsrights"),
            ),
            *args,
            **kwargs
        )


class RightsHolder(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        super(RightsHolder, self).__init__(
            name="RightsHolder",
            namespace="metsrights",
            sub_elements=(Element(name="RightsHolderName", namespace="metsrights"),),
        )
