#!/usr/bin/env python

import logging
import os

from maglib.script.common import (
    MagOperation,
    MagScriptMain,
    MagScriptOptionParser,
)

log = logging.getLogger("set_img_groups")


class Main(MagScriptMain):
    def _build_opt_parser(self):
        return OptionParser()

    def _build_mag_operation(self, options, args):
        return SetImgGroupsOperation(options.overwrite)


class OptionParser(MagScriptOptionParser):
    def __init__(self):
        super().__init__("set img group ID for images missing it")
        self.add_option(
            "--overwrite", help="overwrite existing image groups", action="store_true"
        )


class SetImgGroupsOperation(MagOperation):
    def __init__(self, overwrite):
        super().__init__()
        self._overwrite = overwrite

    def do_op(self, metadigit):
        existing_groups = self._existing_img_groups(metadigit)
        for img in metadigit.img:
            self._set_on_img(img, existing_groups)
            for altimg in img.altimg:
                self._set_on_img(altimg, existing_groups)

    def _set_on_img(self, img, existing_groups):
        detected_group = self._detect_img_group_from_path(img.file[0].href.value)

        if img.imggroupID.value and not self._overwrite:
            log.debug("img already has img group, not overwriting")
            return

        if detected_group not in existing_groups:
            log.warn(
                "detected img group %s does not exist, not setting", detected_group
            )
            return

        log.info("setting img group %s for img", detected_group)
        img.imggroupID.value = detected_group

    @classmethod
    def _existing_img_groups(cls, metadigit):
        groups = set()
        gen = metadigit.gen[0]
        for img_group in gen.img_group:
            groups.add(img_group.ID.value)
        return groups

    @classmethod
    def _detect_img_group_from_path(cls, imgpath):
        path, fname = os.path.split(imgpath)
        prefix, img_group = os.path.split(path)
        return img_group


if __name__ == "__main__":
    import sys
    import logging

    logging.basicConfig(level=logging.WARN)
    main = Main()
    sys.exit(main(sys.argv))
