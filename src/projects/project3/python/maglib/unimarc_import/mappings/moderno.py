# -*- coding: utf-8 -*-

from maglib.unimarc_import.base_readers import MultiSubFieldsIR
from maglib.unimarc_import.mappings.antico import AnticoMapper

class ModernoMapper(AnticoMapper):
    """mappatura per il libro moderno"""
    def _build_readers(self):
        return super(ModernoMapper, self)._build_readers() + (
            MultiSubFieldsIR(
                'subject', '606', ('a', 'x'), separator=' - ', repeat=True),
            MultiSubFieldsIR(
                'subject', '676', ('a', 'c', '9'), separator=' - ', repeat=True),
            )
