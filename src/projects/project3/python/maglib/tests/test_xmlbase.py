"""Tests for maglib.xmlbase module"""


import sys
import unittest

from maglib.xmlbase import Simple_element_instance

PY2 = sys.version_info.major == 2


class SimpleElementInstanceTC(unittest.TestCase):
    def test_to_bytes(self):
        el_instance = Simple_element_instance(name="an-el")
        res = el_instance.to_bytes()
        self.assertIsInstance(res, bytes)
        xml_decl = b"<?xml version='1.0' encoding='utf-8'?>\n"
        self.assertTrue(res.startswith(xml_decl + b"<an-el"))

    def test_to_string(self):
        el_instance = Simple_element_instance(name="an-el")
        res = el_instance.to_string()
        string_type = unicode if PY2 else str  # noqa
        self.assertIsInstance(res, string_type)
        self.assertTrue(u"<an-el")
