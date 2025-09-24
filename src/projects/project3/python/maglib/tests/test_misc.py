

from unittest import TestCase

from maglib.utils.misc import MagResourcePath


class MagResourcePathTC(TestCase):
    def test_get_filepath_dirnames(self):
        get_dirnames = MagResourcePath.get_dirnames
        self.assertEqual(get_dirnames('./A/B/C/D.tif'), ['C', 'B', 'A'])
        self.assertEqual(get_dirnames('a.tif'), [])
        self.assertEqual(get_dirnames('/1/2/3.tif'), ['2', '1'])
        self.assertEqual(get_dirnames('./A/tiff/3.tif'), ['tiff', 'A'])

    def test_simple_path(self):
        path = MagResourcePath(
            'CFI0614830_CF005785227/jpeg300/CFI0614830_CF005785227_0035.jpg')
        self.assertFalse(path.dotslash)
        self.assertEqual(path.mag_dirname, 'CFI0614830_CF005785227')
        self.assertEqual(path.resource_dirname, 'jpeg300')
        self.assertEqual(path.file_basename, 'CFI0614830_CF005785227_0035')
        self.assertEqual(
            path.file_basename_no_prog_part, 'CFI0614830_CF005785227_')
        self.assertEqual(path.file_progressive_part, '0035')
        self.assertEqual(path.file_extension, 'jpg')

    def test_alpha_suffix_path(self):
        path = MagResourcePath(
            './CFI06148/tiff/CFI06148_0035a.tif')
        self.assertTrue(path.dotslash)
        self.assertEqual(path.mag_dirname, 'CFI06148')
        self.assertEqual(path.resource_dirname, 'tiff')
        self.assertEqual(path.file_basename, 'CFI06148_0035a')
        self.assertEqual(path.file_basename_no_prog_part, 'CFI06148_')
        self.assertEqual(path.file_progressive_part, '0035a')
        self.assertEqual(path.file_extension, 'tif')

    def test_alpha_num_path(self):
        path = MagResourcePath(
            './CFI06148/tiff/CFI06148_0035a01.tif')
        self.assertEqual(path.mag_dirname, 'CFI06148')
        self.assertEqual(path.resource_dirname, 'tiff')
        self.assertEqual(path.file_basename, 'CFI06148_0035a01')
        self.assertEqual(path.file_basename_no_prog_part, 'CFI06148_')
        self.assertEqual(path.file_progressive_part, '0035a01')
        self.assertEqual(path.file_extension, 'tif')
