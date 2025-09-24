# -*- coding: utf-8 -*-

import os
import shutil
import tempfile
from os.path import join
from unittest import TestCase

from maglib import Metadigit
from maglib.utils import mag_wrapper
from maglib.utils.resources_import.core import Dirname_img_group, Dirname_usage


class MagDir:
    def __init__(self, subdirs, n_files):
        path = tempfile.mkdtemp()
        self._path = path
        for subdir, extension in subdirs:
            os.mkdir(join(path, subdir))
            for c in range(n_files):
                filename = '%04d.%s' % (c, extension)
                with open(join(path, subdir, filename), 'w'):
                    pass

    @property
    def path(self):
        return self._path

    @property
    def basename(self):
        return os.path.basename(self._path)

    def destroy(self):
        shutil.rmtree(self._path)

    def _touch(self, path):
        with open(path, 'w'):
            pass


class MagDirRecursive(MagDir):
    def __init__(self, contents):
        path = tempfile.mkdtemp()
        self._path = path
        self._mk_struct(path, contents)

    def _mk_struct(self, base, contents):
        if not os.path.isdir(base):
            os.mkdir(base)
        for el in contents:
            if isinstance(el, str):
                self._touch(join(base, el))
            else:
                self._mk_struct(join(base, el['name']), el['children'])


class TestMagDirRecTC(TestCase):
    def test_flat(self):
        d = MagDirRecursive(['1.tif', '1.jpg'])
        self.assertEqual(set(os.listdir(d.path)), {'1.tif', '1.jpg'})
        d.destroy()
        self.assertTrue(not os.path.isdir(d.path))

    def test_recursive(self):
        d = MagDirRecursive(
            [{'name': 'tiff', 'children': ['a.tif', 'b.tif', 'c.tif']},
             {'name': 'jpeg300', 'children': ['a.jpg', 'b.jpg', 'c.jpg']}]
        )
        self.assertEqual(set(os.listdir(d.path)), {'tiff', 'jpeg300'})
        self.assertEqual(
            set(os.listdir(join(d.path, 'tiff'))),
            {'a.tif', 'b.tif', 'c.tif'})
        self.assertEqual(
            set(os.listdir(join(d.path, 'jpeg300'))),
            {'a.jpg', 'b.jpg', 'c.jpg'})

        d.destroy()
        self.assertTrue(not os.path.isdir(d.path))

    def test_complex(self):
        d = MagDirRecursive(
            ['abc.txt', {'name': 'pdf', 'children': ['1.pdf']},
             {'name': 'audio', 'children':
              [{'name': 'wav', 'children': ['0.wav', '1.wav']},
               {'name': 'mp3', 'children': ['0.mp3', '1.mp3']}]}]
        )
        self._assert_dir_content(d.path, ('abc.txt', 'pdf', 'audio'))
        self.assertTrue(os.path.isfile(join(d.path, 'abc.txt')))
        self._assert_dir_content(join(d.path, 'pdf'), ['1.pdf'])
        self._assert_dir_content(join(d.path, 'audio'), ('wav', 'mp3'))
        self._assert_dir_content(
            join(d.path, 'audio', 'wav'), ('0.wav', '1.wav'))
        self._assert_dir_content(
            join(d.path, 'audio', 'mp3'), ('0.mp3', '1.mp3'))
        d.destroy()
        self.assertTrue(not os.path.isdir(d.path))

    def _assert_dir_content(self, path, content):
        self.assertEqual(set(os.listdir(path)), set(content))


class DirnameUsageTC(TestCase):
    """test maglib.utils.resources_import.core.Dirname_usage"""
    def test_simple(self):
        m = Metadigit()
        m.img.add().file.add().href.value = 'A/tiff/1.tif'
        m.img[-1].altimg.add().file.add().href.value = 'A/jpeg/1.jpg'
        m.img.add().file.add().href.value = 'A/tiff/2.tif'
        m.img[-1].altimg.add().file.add().href.value = 'A/jpeg/2.jpg'
        d = Dirname_usage({'^tiff$': ('1',), '^jpeg$': ('3', 'b')})
        self._apply_on_img(m, d)
        self.assertEqual(
            mag_wrapper.get_resource_usages(m.img[0]), ['1'])
        self.assertEqual(
            mag_wrapper.get_resource_usages(m.img[0].altimg[0]), ['3' ,'b'])
        self.assertEqual(
            mag_wrapper.get_resource_usages(m.img[1]), ['1'])
        self.assertEqual(
            mag_wrapper.get_resource_usages(m.img[1].altimg[0]), ['3' ,'b'])

    def test_annidate(self):
        m = Metadigit()
        m.img.add().file.add().href.value = './jpeg300/IIIII/1.jpg'
        m.ocr.add().file.add().href.value = 'PDF/XXXX/1.pdf'
        m.ocr.add().file.add().href.value = 'doc/YYY/1.doc'

        d = Dirname_usage(
            {r'^jpeg(\d+)$': Dirname_usage.DPI_USAGE,
             r'^pdf$': ('3',), r'^doc$': ('2', 'b',)})
        self._apply_on_img(m, d)
        self._apply_on_ocr(m, d)
        self.assertEqual(
            mag_wrapper.get_resource_usages(m.ocr[0]), ['3'])
        self.assertEqual(
            mag_wrapper.get_resource_usages(m.ocr[1]), ['2', 'b'])
        self.assertEqual(
            mag_wrapper.get_resource_usages(m.img[0]), ['2'])

    def _apply_on_img(self, m, dirname_usage):
        for img in m.img:
            dirname_usage.set(img)
            for altimg in img.altimg:
                dirname_usage.set(altimg)

    def _apply_on_ocr(self, m, dirname_usage):
        for ocr in m.ocr:
            dirname_usage.set(ocr)


class DirnameImgGroupTC(TestCase):
    """test for maglib.utils.resources_import.core.Dirname_img_group"""
    def test_simple(self):
        m = Metadigit()
        m.gen.add().img_group.add().ID.value = 'tiff'
        m.img.add().file.add().href.value = './A/tiff/1.tif'
        m.img[-1].altimg.add().file.add().href.value = './A/jpeg300/1.jpg'

        g = Dirname_img_group(m.gen[0].img_group, create_missing=False)
        self._apply_on_img(m, g)
        self.assertEqual(m.img[0].imggroupID.value, 'tiff')
        self.assertEqual(m.img[0].altimg[0].imggroupID.value, None)

        g = Dirname_img_group(m.gen[0].img_group, create_missing=True)
        self._apply_on_img(m, g)
        self.assertEqual(len(m.gen[0].img_group), 2)
        self.assertEqual(m.img[0].imggroupID.value, 'tiff')
        self.assertEqual(m.img[0].altimg[0].imggroupID.value, 'jpeg300')

    def test_annidate(self):
        m = Metadigit()
        m.gen.add()
        m.img.add().file.add().href.value = './B/tiff/C/1.tif'
        m.img.add().file.add().href.value = './thumbs/2.jpg'
        m.img.add().file.add().href.value = '/a/png/Z/3.png'
        m.img.add().file.add().href.value = '/a/unknw//Y/4.tif'

        g = Dirname_img_group(m.gen[0].img_group, create_missing=True)
        self._apply_on_img(m, g)
        self.assertEqual(m.img[0].imggroupID.value, 'tiff')
        self.assertEqual(m.img[1].imggroupID.value, 'thumbs')
        self.assertEqual(m.img[2].imggroupID.value, 'png')
        self.assertEqual(m.img[3].imggroupID.value, None)

    def _apply_on_img(self, m, group):
        for img in m.img:
            group.set(img)
            for altimg in img.altimg:
                group.set(altimg)
