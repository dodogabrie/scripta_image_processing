#-*- coding: utf-8 -*-

"""test per spec_import"""

import os
from unittest import TestCase

from maglib import Metadigit
from maglib.tests.resources_import.test_core import MagDirRecursive
from maglib.utils import mag_wrapper
from maglib.utils.resources_import.core import (
    Dirname_img_group,
    Dirname_usage,
    Static_usage,
)
from maglib.utils.resources_import.spec_import import (
    Audio_importer,
    Images_importer,
    Ocr_importer,
    Resources_dir_spec,
    Video_importer,
)

join = os.path.join


class OcrImporterTC(TestCase):
    """test Ocr_importer"""
    def test_simple(self):
        d = MagDirRecursive([{'name': 'pdf', 'children': ['1.pdf', '2.pdf']}])
        m = Metadigit()
        dir_spec = Resources_dir_spec(
            'pdf', ['pdf'], usage=Static_usage(['2', 'b']))

        importer = Ocr_importer(m.ocr, d.path, [dir_spec])
        importer.do_import()
        d.destroy()

        dname = os.path.basename(d.path)

        self.assertEqual(len(m.ocr), 2)
        self.assertEqual(
            [mag_wrapper.get_resource_filepath(o) for o in m.ocr],
            ['./%s/pdf/1.pdf' % dname, './%s/pdf/2.pdf' % dname])
        self.assertEqual(
            [mag_wrapper.get_resource_usages(o) for o in m.ocr],
            [['2', 'b'], ['2', 'b']])

    def test_multiple(self):
        d = MagDirRecursive([{'name': 'pdf', 'children': ['a.pdf']},
                             {'name': 'doc', 'children': ['b.doc']},
                             {'name': 'docX', 'children': ['c.doc']}])
        m = Metadigit()
        pdf_d_spec = Resources_dir_spec('pdf', ['pdf'])
        doc_d_spec = Resources_dir_spec('doc*', ['doc'])
        importer = Ocr_importer(m.ocr, d.path, [pdf_d_spec, doc_d_spec],
                                dotslash=False)
        importer.do_import()
        d.destroy()

        dname = os.path.basename(d.path)

        self.assertEqual(len(m.ocr), 3)
        self.assertEqual(
            [mag_wrapper.get_resource_filepath(o) for o in m.ocr],
            ['%s/doc/b.doc' % dname, '%s/docX/c.doc' % dname,
             '%s/pdf/a.pdf' % dname])

        self.assertEqual(
            [mag_wrapper.get_resource_usages(o) for o in m.ocr],
            [[], [], []])


class ImgImporterTC(TestCase):
    def test(self):
        d = MagDirRecursive(
            [{'name': 'jpeg300', 'children': ['1.jpg', '2.jpg', '3.jpg']},
             {'name': 'jpeg120', 'children': ['1.jpg', '2.jpg']},
             {'name': 'png', 'children': ['1.png', '2.png', '4.png']}])
        dname = os.path.basename(d.path)
        m = Metadigit()
        m.gen.add_instance()
        u = Dirname_usage.standard
        grp = Dirname_img_group(m.gen[0].img_group, create_missing=True)
        j300_spec = Resources_dir_spec('jpeg300', ['jpg'], u, grp)
        j120_spec = Resources_dir_spec('jpeg120', ['jpg'], u, grp)
        png_spec = Resources_dir_spec('png', ['png'], u, grp)
        importer = Images_importer(
            m.img, d.path, [j300_spec], [j120_spec, png_spec])
        importer.do_import()

        self.assertEqual(len(m.img), 3)
        self.assertEqual(
            [mag_wrapper.get_resource_filepath(i) for i in m.img],
            ['./%s/jpeg300/1.jpg'%dname, './%s/jpeg300/2.jpg'%dname,
             './%s/jpeg300/3.jpg'%dname])
        self.assertEqual(
            [mag_wrapper.get_resource_usages(i) for i in m.img], [['2']]*3)
        self.assertEqual(
            [i.imggroupID.value for i in m.img], ['jpeg300'] * 3)
        self.assertEqual(
            [len(i.altimg) for i in m.img], [2, 2, 0])

        self.assertEqual(
            [mag_wrapper.get_resource_filepath(a) for a in m.img[0].altimg],
            ['./%s/png/1.png'%dname, './%s/jpeg120/1.jpg'%dname])

        # ...
        d.destroy()

    def test_depth(self):
        d = MagDirRecursive(
            [{'name': 'A', 'children':
              [{'name': 'tiff', 'children': ['1.tif']},
               {'name': 'jpeghi', 'children': ['1.jpg']}]}])
        dname = os.path.basename(d.path)
        m = Metadigit()
        tiff_spec = Resources_dir_spec('A/tiff', ['tif'])
        j_spec = Resources_dir_spec('A/jpeghi', 'jpg')
        importer = Images_importer(m.img, d.path, [tiff_spec], [j_spec],
                                   dotslash=False)
        importer.do_import()
        d.destroy()
        self.assertEqual(len(m.img), 1)
        self.assertEqual(
            mag_wrapper.get_resource_filepath(m.img[0]),
            '{}/A/tiff/1.tif'.format(dname)
        )
        self.assertEqual(len(m.img[0].altimg), 1)
        self.assertEqual(
            mag_wrapper.get_resource_filepath(m.img[0].altimg[0]),
            '{}/A/jpeghi/1.jpg'.format(dname)
        )

    def test_strange_paths(self):
        d = MagDirRecursive([
            {'name': 'X', 'children': [
                {'name': 'tiff', 'children': ['A.tif']}
            ]},
            {'name': 'jpeg1', 'children': [
                {'name': 'Y', 'children': ['A.jpg']}
            ]},
            {'name': 'jpeg2', 'children': [
                {'name': 'Y', 'children': ['A.jpg']}
            ]}
        ])
        dname = os.path.basename(d.path)
        m = Metadigit()
        m.gen.add_instance()
        u = Dirname_usage.standard
        grp = Dirname_img_group(m.gen[0].img_group, create_missing=True)
        tiff = Resources_dir_spec('X/tiff', ['tif'], u, grp)
        jpeg = Resources_dir_spec('jpeg*/Y', ['jpg'], u, grp)
        importer = Images_importer(m.img, d.path, [tiff], [jpeg])
        importer.do_import()
        d.destroy()
        self.assertEqual(len(m.img), 1)
        self.assertEqual(
            mag_wrapper.get_resource_filepath(m.img[0]),
            './%s/X/tiff/A.tif' % dname)
        self.assertEqual(m.img[0].imggroupID.value, 'tiff')
        self.assertEqual(mag_wrapper.get_resource_usages(m.img[0]), ['1'])
        self.assertEqual(len(m.img[0].altimg), 2)
        self.assertEqual(
            mag_wrapper.get_resource_filepath(m.img[0].altimg[0]),
            './%s/jpeg2/Y/A.jpg' % dname)
        self.assertEqual(
            mag_wrapper.get_resource_usages(m.img[0].altimg[0]), ['4'])
        self.assertEqual(m.img[0].altimg[0].imggroupID.value, 'jpeg2')
        self.assertEqual(
            mag_wrapper.get_resource_filepath(m.img[0].altimg[1]),
            './%s/jpeg1/Y/A.jpg' % dname)
        self.assertEqual(m.img[0].altimg[1].imggroupID.value, 'jpeg1')
        self.assertEqual(
            mag_wrapper.get_resource_usages(m.img[0].altimg[1]), ['4'])


class AudioImporterTC(TestCase):
    def test1(self):
        d = MagDirRecursive(
            [{'name': 'x', 'children':
              [{'name': 'wav', 'children': ['1.wav']},
               {'name': 'mp3', 'children': ['1.mp3']}]
          }]
        )
        dname = os.path.basename(d.path)
        m = Metadigit()

        wav_spec = Resources_dir_spec('x/wav*', ['wav'])
        mp3_spec = Resources_dir_spec('x/mp3', ['mp3'])
        importer = Audio_importer(m.audio, d.path, [wav_spec], [mp3_spec],
                                  dotslash=False)

        importer.do_import()
        d.destroy()
        self.assertEqual(len(m.audio), 1)
        self.assertEqual(len(m.audio[0].proxies), 2)
        self.assertEqual(
            [mag_wrapper.get_resource_filepath(p) for p in m.audio[0].proxies],
            ['%s/x/wav/1.wav'%dname, '%s/x/mp3/1.mp3'%dname])

class VideoImporterTC(TestCase):
    def test1(self):
        d = MagDirRecursive(
            [{'name': 'x', 'children':
              [{'name': 'y1', 'children': [
                  {'name': 'video1', 'children': ['1.avi']},
                  {'name': 'video2', 'children': ['2.mp4']}
              ]
            }]
          }])
        dname = os.path.basename(d.path)
        m = Metadigit()

        video_spec = Resources_dir_spec('x/y1/video*', ['avi', 'mp4'])
        importer = Video_importer(m.video, d.path, [video_spec], dotslash=False)

        importer.do_import()
        d.destroy()
        self.assertEqual(len(m.video), 2)
        self.assertEqual(
            [len(v.proxies) for v in m.video], [1, 1])
        self.assertEqual(
            [mag_wrapper.get_resource_filepath(v.proxies[0]) for v in m.video],
            ['%s/x/y1/video1/1.avi'%dname, '%s/x/y1/video2/2.mp4'%dname])
