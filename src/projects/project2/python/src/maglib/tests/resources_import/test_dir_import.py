# -*- coding: utf-8 -*-

import os
from unittest import TestCase

from maglib import Metadigit
from maglib.tests.resources_import.test_core import MagDirRecursive
from maglib.utils import mag_wrapper
from maglib.utils.resources_import.core import (Dirname_img_group,
                                                Dirname_usage,
                                                Resources_directory,
                                                Static_usage)
from maglib.utils.resources_import.dir_import import (Dir_audio_importer,
                                                      Dir_docs_importer,
                                                      Dir_images_importer)

join = os.path.join
basename = os.path.basename



class DirDocsImporterTC(TestCase):
    """test for maglib.utils.resources_import.dir_import.Dir_docs_importer"""
    def test_simple(self):
        d = MagDirRecursive(
            [{'name': 'pdf', 'children': ['a.pdf', 'b.pdf']}])
        m = Metadigit()
        resources_dir = Resources_directory(
            join(d.path, 'pdf'), ['pdf'], './AA/pdf',
            Static_usage(('3', 'b')))

        dir_importer = Dir_docs_importer(m.doc, resources_dir)
        dir_importer.do_import()
        d.destroy()

        self.assertEqual(len(m.doc), 2)
        self.assertEqual(mag_wrapper.get_resource_filepath(m.doc[0]),
                          './AA/pdf/a.pdf')
        self.assertEqual(mag_wrapper.get_resource_filepath(m.doc[1]),
                          './AA/pdf/b.pdf')
        self.assertEqual(mag_wrapper.get_resource_usages(m.doc[0]),
                          ['3', 'b'])
        self.assertEqual(mag_wrapper.get_resource_usages(m.doc[1]),
                          ['3', 'b'])



class DirImgsImporterTC(TestCase):
    """test for maglib.utils.resources_import.core.Dir_imgs_importer"""
    def test_simple(self):
        d = MagDirRecursive(
            [{'name': 'tiff', 'children': ['1.tif', '2.tif']},
             {'name': 'jpeg300', 'children': ['1.jpg', '2.jpg']},
             {'name': 'jpeg120', 'children': ['1.jpg', '2.jpg']},
             {'name': 'png', 'children': ['1.png', '2.png']},
             {'name': 'thumbs', 'children': ['1.jpg', '2.jpg']}])

        m = Metadigit()
        m.gen.add()
        tiff = Resources_directory(
            join(d.path, 'tiff'), ['tif'], './BB/tiff',
            Dirname_usage.standard,
            Dirname_img_group(m.gen[0].img_group, create_missing=True))
        jpeg300 = Resources_directory(
            join(d.path, 'jpeg300'), ['jpg'], './BB/jpeg300',
            Dirname_usage.standard,
            Dirname_img_group(m.gen[0].img_group, create_missing=True))
        jpeg120 = Resources_directory(
            join(d.path, 'jpeg120'), ['jpg'], './BB/jpeg120',
            Dirname_usage.standard,
            Dirname_img_group(m.gen[0].img_group, create_missing=True))
        png = Resources_directory(
            join(d.path, 'png'), ['png'], './BB/png',
            Dirname_usage.standard,
            Dirname_img_group(m.gen[0].img_group, create_missing=True))
        thumbs = Resources_directory(
            join(d.path, 'thumbs'), ['jpg'], './BB/thumbs',
            Dirname_usage.standard,
            Dirname_img_group(m.gen[0].img_group, create_missing=False))

        importer = Dir_images_importer(
            m.img, tiff, (jpeg300, jpeg120, png, thumbs))

        importer.do_import()
        d.destroy()

        self.assertEqual(len(m.img), 2)
        self.assertEqual(mag_wrapper.get_resource_filepath(m.img[0]),
                          './BB/tiff/1.tif')
        self.assertEqual(mag_wrapper.get_resource_filepath(m.img[1]),
                          './BB/tiff/2.tif')
        self.assertEqual(m.img[0].imggroupID.value, 'tiff')
        self.assertEqual(m.img[1].imggroupID.value, 'tiff')
        self.assertEqual(mag_wrapper.get_resource_usages(m.img[0]), ['1'])
        self.assertEqual(mag_wrapper.get_resource_usages(m.img[1]), ['1'])
        self.assertEqual(len(m.img[0].altimg), 4)
        self.assertEqual(len(m.img[1].altimg), 4)
        self.assertEqual(m.img[0].imggroupID.value, 'tiff')
        self.assertEqual(m.img[1].imggroupID.value, 'tiff')
        self.assertEqual(
            [aimg.imggroupID.value for aimg in m.img[0].altimg],
            ['png', 'jpeg300', 'jpeg120', None])
        self.assertEqual(
            [aimg.imggroupID.value for aimg in m.img[1].altimg],
            ['png', 'jpeg300', 'jpeg120', None])
        self.assertEqual([mag_wrapper.get_resource_filepath(aimg)
                           for aimg in m.img[0].altimg],
                          ['./BB/png/1.png', './BB/jpeg300/1.jpg',
                           './BB/jpeg120/1.jpg', './BB/thumbs/1.jpg'])
        self.assertEqual([mag_wrapper.get_resource_filepath(aimg)
                           for aimg in m.img[1].altimg],
                          ['./BB/png/2.png', './BB/jpeg300/2.jpg',
                           './BB/jpeg120/2.jpg', './BB/thumbs/2.jpg'])
        self.assertEqual([mag_wrapper.get_resource_usages(aimg)
                           for aimg in m.img[0].altimg],
                          [['2'], ['2'], ['3'], ['4']])


class DirAudioImporterTC(TestCase):
    """test for maglib.utils.resources_import.core.Dir_audio_importer"""
    def test_flat(self):
        d = MagDirRecursive(
            [{'name': 'wav', 'children': ['1.wav', '2.wave']}])
        m = Metadigit()
        wav_dir = Resources_directory(
            join(d.path, 'wav'), ['wav', 'wave'], 'XX/132/wav',
            Static_usage(['1']))

        importer = Dir_audio_importer(m.audio, wav_dir)
        importer.do_import()
        d.destroy()

        self.assertEqual(len(m.audio), 2)
        self.assertEqual([len(a.proxies) for a in m.audio], [1, 1])
        self.assertEqual(
            [mag_wrapper.get_all_resource_filepath(a) for a in m.audio],
            ['XX/132/wav/1.wav', 'XX/132/wav/2.wave'])
        self.assertEqual(
            [mag_wrapper.get_resource_usages(a.proxies[0]) for a in m.audio],
            [['1'], ['1']])

    def test_alt_proxies(self):
        d = MagDirRecursive(
            [{'name': 'wav', 'children': ['a.wav']},
             {'name': 'mp3', 'children': ['a.mp3', 'b.mp3']}])
        m = Metadigit()
        wav_dir = Resources_directory(
            join(d.path, 'wav'), ['wav'], './W/wav',
            Static_usage(['1']))
        mp3_dir = Resources_directory(
            join(d.path, 'mp3'), ['mp3'], './W/mp3',
            Static_usage(['2', 'b']))

        importer = Dir_audio_importer(m.audio, wav_dir, [mp3_dir])
        importer.do_import()
        d.destroy()

        self.assertEqual(len(m.audio), 1)
        self.assertEqual(len(m.audio[0].proxies), 2)
        self.assertEqual(
            [mag_wrapper.get_all_resource_filepath(p)
             for p in m.audio[0].proxies],
            ['./W/wav/a.wav', './W/mp3/a.mp3'])
        self.assertEqual(
            [mag_wrapper.get_resource_usages(p) for p in m.audio[0].proxies],
            [['1'], ['2', 'b']])





# class ImgImportTC(TestCase):
#     def test_simple(self):
#         dIr = MagDir([('tiff', 'tif'), ('jpeg150', 'jpg')], 4)
#         opts = ImageImportOptions(['tiff'], ['jpeg150'], create_groups=True)
#         m = Metadigit()
#         runner = ImageImportRunner(m, dIr.path, opts)
#         runner.run()

#         self.assertEqual(len(m.img), 4)
#         for i, img in enumerate(m.img):
#             self.assertEqual(
#                 img.file[0].href.value,
#                 join('.', basename(dIr.path), 'tiff', '%04d.tif' % i))
#             self.assertEqual(img.imggroupID.value, 'tiff')
#             self.assertEqual(set(u.value for u in img.usage), set(['1']))
#             self.assertEqual(len(img.altimg), 1)
#             aimg = img.altimg[0]
#             self.assertEqual(
#                 aimg.file[0].href.value,
#                 join('.', basename(dIr.path), 'jpeg150', '%04d.jpg' % i))
#             self.assertEqual(aimg.imggroupID.value, 'jpeg150')
#             self.assertEqual(set(u.value for u in aimg.usage), set(['3']))

#         dIr.destroy()

#     def test_complex(self):
#         dIr = MagDir(
#             [('tiff', 'tif'), ('jpeg300', 'jpg'), ('jpeg150', 'jpg'),
#              ('png', 'png'), ('thumbs', 'jpg')], 2)
#         opts = ImageImportOptions(
#             ['tiff', 'tifflzw'], ['jpeg*', 'png', 'thumbs'])
#         m = Metadigit()
#         runner = ImageImportRunner(m, dIr.path, opts)
#         runner.run()

#         self.assertEqual(len(m.img), 2)
#         for i, img in enumerate(m.img):
#             self.assertEqual(len(img.altimg), 4)

#             self.assertEqual(
#                 img.altimg[0].file[0].href.value,
#                 join('.', basename(dIr.path), 'png', '%04d.png' % i))
#             self.assertEqual(
#                 set(u.value for u in img.altimg[0].usage), set(['2']))
#             self.assertEqual(
#                 img.altimg[1].file[0].href.value,
#                 join('.', basename(dIr.path), 'jpeg300', '%04d.jpg' % i))
#             self.assertEqual(
#                 set(u.value for u in img.altimg[1].usage), set(['2']))
#             self.assertEqual(
#                 img.altimg[2].file[0].href.value,
#                 join('.', basename(dIr.path), 'jpeg150', '%04d.jpg' % i))
#             self.assertEqual(
#                 set(u.value for u in img.altimg[2].usage), set(['3']))
#             self.assertEqual(
#                 img.altimg[3].file[0].href.value,
#                 join('.', basename(dIr.path), 'thumbs', '%04d.jpg' % i))
#             self.assertEqual(
#                 set(u.value for u in img.altimg[3].usage), set(['4']))

#         dIr.destroy()

#     def test_master_jpeg(self):
#         dIr = MagDir([('jpeg300', 'jpg'), ('jpeg100', 'jpg')], 3)
#         opts = ImageImportOptions(['jpeg300'], ['jpeg100'])
#         m = Metadigit()
#         runner = ImageImportRunner(m, dIr.path, opts)
#         runner.run()

#         self.assertEqual(len(m.img), 3)
#         for i, img in enumerate(m.img):
#             self.assertEqual(
#                 img.file[0].href.value,
#                 join('.', basename(dIr.path), 'jpeg300', '%04d.jpg' % i))
#             self.assertEqual(len(img.altimg), 1)
#             self.assertEqual(
#                 img.altimg[0].file[0].href.value,
#                 join('.', basename(dIr.path), 'jpeg100', '%04d.jpg' % i))

#         dIr.destroy()
