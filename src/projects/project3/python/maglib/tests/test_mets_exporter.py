import configparser
import operator
import unittest

from maglib import Metadigit
from maglib.mag.mag_elements import Gen
from maglib.mets_export import MetsExporter, MetsHdrBuilder
from maglib.mets_export.info_extract import (
    AgentsInfoConfigReader,
    MODSMappingReader,
)
from maglib.mets_export.xmlutils import XmlUtils


class MetsExporterTC(unittest.TestCase):
    def test_base(self):
        m = Metadigit()
        exporter = MetsExporter(m)
        exporter.convert()

    def test_convert_into(self):
        mets = XmlUtils.create_element("mets")
        mets.attrib["OBJID"] = "myobj"
        mets.append(XmlUtils.create_element("altRecordID"))
        mets[-1].text = "an id"

        m = Metadigit()
        exporter = MetsExporter(m, export_into=mets)
        exporter.convert()

        self.assertIs(mets, exporter.mets)
        self.assertEqual(mets.attrib["OBJID"], "myobj")
        self.assertEqual(XmlUtils.xpath(mets, "mets:altRecordID[1]/text()"), ["an id"])
        self.assertTrue(XmlUtils.xpath(mets, "mets:structMap"))

    def test_rights_from_info_parser(self):
        m = Metadigit()
        info_parser = _build_configparser(
            u"[rights]",
            "id = rId",
            "label = rLabel",
            "rights_holder_name = 0",
            "rights_holder_description =",
            "rights_holder_address =",
        )
        exporter = MetsExporter(m, info_parser=info_parser)
        exporter.convert()
        mets = exporter.mets

        ns = {"mets": "http://www.loc.gov/METS/"}

        rights_md_el = mets.xpath("//mets:rightsMD", namespaces=ns)[0]
        self.assertEqual(rights_md_el.attrib["ID"], "rId")


class AgentsConfigReaderTC(unittest.TestCase):
    def test_single_agent(self):
        cfg_parser = _build_configparser(
            u"[agent:0]", "role = r0", "type = t0", "name =Foo"
        )

        reader = AgentsInfoConfigReader()

        agents = reader.read(cfg_parser)
        self.assertEqual(
            agents,
            [
                {
                    "role": "r0",
                    "type": "t0",
                    "name": "Foo",
                    "otherrole": None,
                    "id": None,
                }
            ],
        )


class MetsHdrBuilderTC(unittest.TestCase):
    def test_base(self):
        agents_info = [
            {"role": "r0", "type": "t0", "name": "Foo"},
            {
                "role": "r1",
                "type": "t1",
                "name": "Bar Baz",
                "id": "i1",
                "otherrole": "or1",
            },
        ]
        builder = MetsHdrBuilder()
        mets_hdr = builder.build(Gen(), agents_info)

        self.assertTrue(mets_hdr.tag.endswith("metsHdr"))
        self.assertEqual(len(mets_hdr), 2)
        self.assertTrue(mets_hdr[0].tag.endswith("agent"))
        self.assertTrue(mets_hdr[0][0].tag.endswith("name"))
        self.assertEqual(mets_hdr[0][0].text, "Foo")
        self.assertNotIn("OTHERROLE", mets_hdr[0].attrib)

        self.assertTrue(mets_hdr[1].tag.endswith("agent"))
        self.assertTrue(mets_hdr[1][0].tag.endswith("name"))
        self.assertEqual(mets_hdr[1][0].text, "Bar Baz")
        self.assertEqual(mets_hdr[1].attrib["OTHERROLE"], "or1")


class MODSMappingReaderTC(unittest.TestCase):
    def test_base(self):
        bib = Metadigit().bib.add_instance()
        bib.identifier.add_instance().value = "ID00"
        bib.holdings.add_instance().library.add_instance().value = "lib"

        reader = MODSMappingReader(
            {"identifier": "identifier", "identifier_cont": "library"}
        )

        mods_info = reader.read(bib)
        self.assertEqual(
            sorted(mods_info, key=operator.itemgetter("text")),
            [
                {"text": "ID00", "field": "identifier"},
                {"text": "lib", "type": "cont", "field": "identifier"},
            ],
        )


def _build_configparser(*lines):
    ini = u"\n".join(lines)
    cfg_parser = configparser.ConfigParser()
    cfg_parser.read_string(ini)
    return cfg_parser
