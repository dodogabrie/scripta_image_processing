#!/usr/bin/env python

import logging
import os

from maglib.script.common import (
    MagOperation,
    MagScriptMain,
    MagScriptOptionParser,
)
from maglib.utils.mag_wrapper import (
    get_resource_sequence_number,
    set_resource_sequence_number,
)


class Main(MagScriptMain):
    def _build_opt_parser(self):
        return OptionParser()

    def _build_mag_operation(self, options, args):
        return SetSequenceNumberOperation(options.keep_existing, options.first_seqn)


class OptionParser(MagScriptOptionParser):
    def __init__(self):
        super().__init__("set resource sequence numbers")
        self.add_option(
            "--keep-existing",
            help="keep existing sequence numbers",
            action="store_true",
        )
        self.add_option(
            "--first-seqn", help="first sequence number of the sequence", default=1
        )


class SetSequenceNumberOperation(MagOperation):
    def __init__(self, keep_existing: bool = False, first_seqn: int = 1):
        self._keep_existing = keep_existing
        self._first_seqn = first_seqn

    def do_op(self, metadigit) -> None:
        self._do_resource_type(metadigit.img)
        self._do_resource_type(metadigit.doc)
        self._do_resource_type(metadigit.ocr)
        self._do_resource_type(metadigit.audio)
        self._do_resource_type(metadigit.video)
        self._do_resource_type(metadigit.video)

    def _do_resource_type(self, node) -> None:
        for i, rsrc in enumerate(node, self._first_seqn):
            if not self._keep_existing or not get_resource_sequence_number(rsrc):
                set_resource_sequence_number(rsrc, i)


if __name__ == "__main__":
    import sys
    import logging

    logging.basicConfig(level=logging.WARN)
    main = Main()
    sys.exit(main(sys.argv))
