# -*- coding: utf-8 -*-

"""test per resources_import.wizard"""

import os
from unittest import TestCase

from maglib import Metadigit
from maglib.tests.resources_import.test_core import MagDirRecursive
from maglib.utils import mag_wrapper
from maglib.utils.resources_import.wizard import (AudioImportOptions,
                                                  AudioImportRunner,
                                                  DocImportOptions,
                                                  DocImportRunner,
                                                  ImageImportOptions,
                                                  ImageImportRunner,
                                                  OcrImportOptions,
                                                  OcrImportRunner,
                                                  VideoImportOptions,
                                                  VideoImportRunner)


class DocImportTC(TestCase):
    def test_basic(self):
        d = MagDirRecursive(
            [{'name': 'doc', 'children': ['1.pdf', '1.doc']}])
        m = Metadigit()
        dname = os.path.basename(d.path)

        opts = DocImportOptions(subdirs=['doc'], usages=['2'])
        runner = DocImportRunner(m, d.path, opts)
        runner.run()
        d.destroy()

        self.assertEqual(len(m.doc), 2)
        self.assertEqual(
            [mag_wrapper.get_resource_filepath(d) for d in m.doc],
            ['./%s/doc/1.doc'%dname, './%s/doc/1.pdf'%dname])
        self.assertEqual(
            [mag_wrapper.get_resource_usages(d) for d in m.doc],
            [['2'], ['2']])


class OcrImportTC(TestCase):
    def test_depth(self):
        d = MagDirRecursive(
            [{'name': 'pdf', 'children': ['1.pdf']},
             {'name': 'docI', 'children': [
                 {'name': 'FOO', 'children': ['A.xml', 'B.docx']}
             ]}
         ])
        m = Metadigit()

        opts = OcrImportOptions(
            dotslash=False, subdirs=['pdf', 'doc*/FOO'], usages=['3', 'b'])
        runner = OcrImportRunner(m, d.path, opts)
        runner.run()
        d.destroy()

        # .docx ignored
        self.assertEqual(len(m.ocr), 2)
        self.assertEqual(
            [mag_wrapper.get_resource_filepath(o) for o in m.ocr],
            ['%s/docI/FOO/A.xml'%d.basename, '%s/pdf/1.pdf'%d.basename])
        self.assertEqual(
            [mag_wrapper.get_resource_usages(o) for o in m.ocr],
            [['3', 'b']] * 2)


class ImageImportTC(TestCase):
    def test1(self):
        d = MagDirRecursive([
            {'name': 'A', 'children': [
                {'name': 'jpegHI', 'children': ['1.jpg', '2.jpg']}
            ]},
            {'name': 'jpegLO', 'children': ['1.jpg', '2.jpg']}
         ])
        m = Metadigit()

        opts = ImageImportOptions(
            subdirs=['A/jpegHI'], alt_subdirs=['jpegLO'], create_groups=True,
            extra_path_levels=0)
        runner = ImageImportRunner(m, d.path, opts)
        runner.run()
        d.destroy()

        self.assertEqual(len(m.gen[0].img_group), 2)
        self.assertEqual(
            [g.ID.value for g in m.gen[0].img_group], ['jpegHI', 'jpegLO'])

        self.assertEqual(len(m.img), 2)
        self.assertEqual(
            [mag_wrapper.get_resource_filepath(i) for i in m.img],
            ['./A/jpegHI/1.jpg', './A/jpegHI/2.jpg'])
        self.assertEqual(
            [mag_wrapper.get_resource_usages(i) for i in m.img],
            [[], []])
        self.assertEqual(
            [i.imggroupID.value for i in m.img],
            ['jpegHI'] * 2)

        self.assertEqual([len(i.altimg) for i in m.img], [1, 1])
        self.assertEqual(
            [len(i.altimg) for i in m.img], [1, 1])
        self.assertEqual(
            [mag_wrapper.get_resource_filepath(i.altimg[0]) for i in m.img],
            ['./jpegLO/1.jpg', './jpegLO/2.jpg'])
        self.assertEqual(
            [mag_wrapper.get_resource_usages(i.altimg[0]) for i in m.img],
            [[], []])
        self.assertEqual(
            [i.altimg[0].imggroupID.value for i in m.img],
            ['jpegLO'] * 2)



class VideoImportTC(TestCase):
    def test1(self):
        d = MagDirRecursive([
            {'name': 'master', 'children': ['a.avi']},
            {'name': 'preview', 'children': [
                {'name': '1', 'children': ['a.mp4']},
                {'name': '2', 'children': ['a.wmv']}
            ]}
        ])
        m = Metadigit()
        opts = VideoImportOptions(
            subdirs=['master'], alt_subdirs=['preview/*'])
        runner = VideoImportRunner(m, d.path, opts)
        runner.run()
        d.destroy()

        self.assertEqual(len(m.video),1)
        self.assertEqual(len(m.video[0].proxies), 3)

        self.assertEqual(
            [mag_wrapper.get_resource_filepath(p) for p in m.video[0].proxies],
            ['./%s/master/a.avi'%d.basename, './%s/preview/1/a.mp4'%d.basename,
             './%s/preview/2/a.wmv'%d.basename])
        self.assertEqual(
            [mag_wrapper.get_resource_usages(p) for p in m.video[0].proxies],
            [[]]* 3)


class AudioImportTC(TestCase):
    def test1(self):
        d = MagDirRecursive([
            {'name': 'audio', 'children': ['1.mp3', '2.wav']}
        ])
        m = Metadigit()
        opts = AudioImportOptions(
            subdirs=['audio'], usages=['1', 'b'], extra_path_levels=2,
            dotslash=False)
        runner = AudioImportRunner(m, d.path, opts)
        runner.run()
        d.destroy()

        d_parent_basename = os.path.basename(os.path.dirname(d.path))
        self.assertEqual(len(m.audio), 2)
        self.assertEqual([len(a.proxies) for a in m.audio], [1, 1])
        self.assertEqual(
            [mag_wrapper.get_resource_filepath(a.proxies[0]) for a in m.audio],
            ['%s/%s/audio/1.mp3' % (d_parent_basename, d.basename),
             '%s/%s/audio/2.wav' % (d_parent_basename, d.basename)])
        self.assertEqual(
            [mag_wrapper.get_resource_usages(a.proxies[0]) for a in m.audio],
            [['1', 'b']] * 2)


class RootImportTC(TestCase):
    def test_simple(self):
        d = MagDirRecursive(['1.tif', '2.tif'])
        m = Metadigit()
        opts = ImageImportOptions(subdirs=['.'])
        runner = ImageImportRunner(m, d.path, opts)
        runner.run()
        d.destroy()

        self.assertEqual(len(m.img), 2)
        self.assertEqual(
            [mag_wrapper.get_resource_filepath(i) for i in m.img],
            ['./%s/1.tif'%d.basename, './%s/2.tif'%d.basename])

    def test_mess(self):
        d = MagDirRecursive(
            ['1.mp4', {'name': 'lowres', 'children': ['1.avi']}])
        m = Metadigit()
        opts = VideoImportOptions(subdirs=[''], alt_subdirs=['lowres'],
                                  dotslash=False)
        runner = VideoImportRunner(m, d.path, opts)
        runner.run()
        d.destroy()

        self.assertEqual(len(m.video), 1)
        self.assertEqual(len(m.video[0].proxies), 2)

        self.assertEqual(
            [mag_wrapper.get_resource_filepath(p) for p in m.video[0].proxies],
            ['%s/1.mp4'%d.basename, '%s/lowres/1.avi'%d.basename])


class ProjDirImport(TestCase):
    """importazione che simula quella dalla directory del progetto e
    non da quella del documento"""
    def test(self):
        # d è la directory del progetto
        d = MagDirRecursive([
            {'name': 'd1', 'children': [
                {'name': 'tiff', 'children': ['1.tif']},
                {'name': 'jpeg', 'children': ['1.jpg']}]},
            {'name': 'd2', 'children': [
                {'name': 'xx', 'children': [
                    {'name': 'docs', 'children': ['a.html']}]
             }]}
        ])

        m = Metadigit()
        opts = ImageImportOptions(alt_subdirs=['d1/jpe*'], subdirs=['d1/tiff'],
                                  extra_path_levels=0)
        runner = ImageImportRunner(m, d.path, opts)
        runner.run()


        self.assertEqual(len(m.img), 1)
        self.assertEqual(mag_wrapper.get_resource_filepath(m.img[0]),
                          './d1/tiff/1.tif')
        self.assertEqual(len(m.img[0].altimg), 1)
        self.assertEqual(mag_wrapper.get_resource_filepath(m.img[0].altimg[0]),
                          './d1/jpeg/1.jpg')

        opts = DocImportOptions(subdirs=['d2/xx/docs'], extra_path_levels=0)
        runner = DocImportRunner(m, d.path, opts)
        runner.run()

        self.assertEqual(len(m.doc), 1)
        self.assertEqual(mag_wrapper.get_resource_filepath(m.doc[0]),
                          './d2/xx/docs/a.html')

        d.destroy()
