import unittest

from lxml import etree

from maglib.mag.mag_elements import ExtraCommentSerde, Metadigit
from maglib.xmlbase import NAMESPACES


class MetadigitTC(unittest.TestCase):
    def test_mets(self):
        m = Metadigit()
        m.extra.add_instance()

        mets = m.extra[0].mets.add_instance()
        mets.metsHdr.add_instance()

        mets.metsHdr[0].agent.add_instance()

        mets.metsHdr[0].agent[0].TYPE.value = "t000"
        mets.metsHdr[0].agent[0].name.add_instance().value = "foo"

        mods_mdwrap = mets.dmdSec.add_instance().mdWrap.add_instance()

        mods = mods_mdwrap.xmlData.add_instance().mods.add_instance()

        mods.identifier.add_instance().value = "ID0"
        mods.identifier.add_instance().value = "ID1"
        mods.identifier[0].type.value = "SUBSIS"

        # rights
        amd_sec = mets.amdSec.add_instance()
        rights_mdwrap = amd_sec.rightsMD.add_instance().mdWrap.add_instance()
        rights_decl = (
            rights_mdwrap.xmlData.add_instance().RightsDeclarationMD.add_instance()
        )

        rights_decl.RIGHTSCATEGORY.value = "RR"
        rights_holder = rights_decl.RightsHolder.add_instance()
        rights_holder.RightsHolderName.add_instance().value = "rhn"

        xml_string = m.to_string(pretty_print=True)

        self.assertTrue("<mods:identifier" in xml_string)
        self.assertTrue("<extra>" in xml_string)
        self.assertTrue("<metsrights:RightsHolderName>" in xml_string)

    def test_only_one_extra_is_allowed(self):
        m = Metadigit()
        m.extra.add_instance()
        with self.assertRaises(RuntimeError):
            m.extra.add_instance()


class ExtraElementCommentSerde(unittest.TestCase):
    def test_serialize(self):
        m = Metadigit()
        extra_inst = _fill_extra(m)

        comment_el = ExtraCommentSerde.serialize(extra_inst)
        self.assertEqual(comment_el.tag, etree.Comment)

        self.assertTrue(comment_el.text.startswith("##mag <extra> element"))

    def test_serialize_deserialize(self):
        m = Metadigit()
        extra_inst = _fill_extra(m)

        comment_el = ExtraCommentSerde.serialize(extra_inst)

        # deserialization needs a containing xml element
        containing_el = etree.Element("a")
        containing_el.append(etree.Element("b"))
        containing_el.append(etree.Comment("other comment"))
        containing_el.append(comment_el)
        containing_el.append(etree.Comment("other comment2"))

        reloaded_extra_inst = ExtraCommentSerde.deserialize(containing_el)
        self.assertEqual(
            reloaded_extra_inst.mets[0].metsHdr[0].agent[0].name[0].value, "ag-0"
        )
        self.assertEqual(extra_inst.to_string(), reloaded_extra_inst.to_string())


class ExtraSerializationTC(unittest.TestCase):
    """Test serialization and loading of <extra> element"""

    def test_extra_serialization(self):
        m = Metadigit()
        _fill_extra(m)
        el = m.as_xml()

        # <mag:extra> is not in out xml
        self.assertFalse(el.xpath("//mag:extra", namespaces=NAMESPACES))
        self.assertEqual(len(list(el.iter(tag=etree.Comment))), 1)

        mag_string = m.to_string()
        m = Metadigit.from_xml_string(mag_string)
        self.assertEqual(len(m.extra), 1)
        self.assertEqual(m.extra[0].mets[0].metsHdr[0].agent[0].name[0].value, "ag-0")


def _fill_extra(metadigit):
    metadigit.extra.add_instance()
    mets = metadigit.extra[0].mets.add_instance()
    mets.metsHdr.add_instance()
    mets.metsHdr[0].agent.add_instance()
    mets.metsHdr[0].agent[0].name.add_instance().value = "ag-0"
    return metadigit.extra[0]
