#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import os

from maglib.lint import *
from maglib.script.common import (
    MagInfoReader,
    MagOperation,
    MagScriptInfoFileOptParser,
    MagScriptMain,
)


class MagLintOperation(MagOperation):
    write_mag = False

    def __init__(self, mag_lint, mag_name=None):
        self._mag_lint = mag_lint
        self._mag_name = mag_name

    def do_op(self, metadigit):
        errors = self._mag_lint.test(metadigit)
        if errors:
            for err in errors:
                print(err)
            msg = 'il mag%s ha errori' % (
                ' %s' % self._mag_name if self._mag_name else '')
            print(msg)
            return 3


class MagLintMain(MagScriptMain):
    def _build_opt_parser(self):
        return MagLintOptParser()

    def _build_mag_operation(self, options, args):
        if options.info_file:
            info = MagLintInfoFileReader.read_file(options.info_file)
        else:
            info = {}
        info['schema_validation'] = not options.skip_schema_validation
        info['mag_path'] = options.input
        if not options.skip_prefix:
            info['files_prefix'] = os.path.splitext(
                os.path.basename(options.input))[0]
        info['stop_on_first_fail'] = options.stop_on_first_fail
        info['test_files'] = not options.skip_files
        info['test_md5'] = options.test_md5
        if options.mag_dir:
            info['mag_dir'] = options.mag_dir
        info['test_dir_contents'] = not options.skip_dir_contents

        mag_lint = MagLintBuilder.from_info_dict(info)
        return MagLintOperation(mag_lint, options.input)


class MagLintOptParser(MagScriptInfoFileOptParser):
    def __init__(self, *args, **kwargs):
        MagScriptInfoFileOptParser.__init__(self, *args, **kwargs)
        self.remove_options('--output', '--clean')
        self.set_options_required('--input')
        self.set_options_unrequired('--info-file')
        self.add_option(
            '-s', '--stop-on-first-fail', action='store_true', default=False,
            help='interrompi il test al primo fallimento')
        self.add_option(
            '-X', '--skip-schema-validation', action='store_true',
            default=False, help='non effettuare la validazione nei confronti '
            'dello schema xsd mag')
        self.add_option(
            '-m', '--test-md5', action='store_true',
            help='testa gli md5 dei file del mag')
        self.add_option('-F', '--skip-files', action='store_true',
                        help='non eseguire i test sui file del mag')
        self.add_option('-P', '--skip-prefix', action='store_true',
                        help='non eseguire test sul prefisso dei file')
        self.add_option(
            '-D', '--skip-dir-contents', action='store_true',
            help='non eseguire il test sul contenuto della directory del mag')
        self.add_option(
            '-d', '--mag-dir', action='store',
            help='directory del per il controllo del contenuto, '
            '(default filename mag senza .xml)')


class MagLintInfoFileReader(MagInfoReader):
    @classmethod
    def _read_value(cls, key, value, encoding):
        readed = super(MagLintInfoFileReader, cls)._read_value(
            key, value, encoding)
        if key == 'img_groups':
            return cls._read_list_value(readed)
        if key == 'ocr_usages':
            return cls._read_list_value(readed)
        if key == 'img_usages':
            usages_lists = []
            for usages in cls._read_list_value(readed, separator=';'):
                usages_lists.append(
                    cls._read_list_value(usages, separator=','))
            return usages_lists
        return readed

    @classmethod
    def _read_list_value(cls, value, separator=','):
        return value.split(separator)


class MagLintBuilder(object):
    @classmethod
    def from_info_dict(cls, info):
        """costruisce MagLint a partire da un dizionario :info:
        chiavi: mag_path, img_groups, img_usages, files_prefix, mag_dir

        booleani:
        stop_on_first_fail, test_files, test_md5, test_dir_contents,
        shema_validatation"""
        tests = []
        stop_on_first_fail = info.get('stop_on_first_fail', False)

        if info.get('schema_validation'):
            tests.append(SchemaTest())

        gen_test_keys = ('stprog', 'collection', 'agency',
                         'completeness', 'access_rights')
        gen_test_dict = dict((k, v) for k, v in info.items()
                             if k in gen_test_keys)

        mag_dir = os.path.dirname(info['mag_path']) \
            if info.get('mag_path') else None

        if gen_test_dict:
            tests.append(GenTest(gen_test_dict))
        if info.get('img_groups'):
            tests.append(ImgGroupsTest(info['img_groups']))
            tests.append(ImgTestGroups(info['img_groups'], stop_on_first_fail))
        if info.get('img_usages'):
            tests.append(ImgUsageTest(info['img_usages'], stop_on_first_fail))
        if info.get('ocr_usages'):
            tests.append(OcrUsageTest(info['ocr_usages']))

        if info.get('library'):
            tests.append(LibraryTest(info['library']))

        if info.get('files_prefix'):
            mag_name = os.path.splitext(os.path.basename(info['mag_path']))[0]
            tests.append(ImgFilenameTest('^%s' % mag_name, stop_on_first_fail))
            tests.append(OcrFilenameTest('^%s' % mag_name, stop_on_first_fail))
        if mag_dir is not None and info.get('test_files'):
            tests.append(ImgFilesTest(mag_dir, stop_on_first_fail))
            tests.append(ImgSizeTest(mag_dir, stop_on_first_fail))
            tests.append(ImgPixelSizeTest(mag_dir, stop_on_first_fail))
            tests.append(OcrFilesTest(mag_dir, stop_on_first_fail))
            tests.append(OcrSizeTest(mag_dir, stop_on_first_fail))
            if info.get('test_dir_contents'):
                tests.append(VolDirContentsTest(
                    info.get('mag_dir') or
                    os.path.splitext(info['mag_path'])[0]))
        if mag_dir is not None and info.get('test_md5'):
            tests.append(ImgMd5Test(mag_dir, stop_on_first_fail))
            tests.append(OcrMd5Test(mag_dir, stop_on_first_fail))

        return MagLint(tests, stop_on_first_fail)


if __name__ == '__main__':
    import sys

    main = MagLintMain()
    sys.exit(main(sys.argv))
