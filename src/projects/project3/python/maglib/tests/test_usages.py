# -*- coding: utf-8 -*-


"""testa modulo maglib.utils.usages"""

from unittest import TestCase

from maglib import Metadigit
from maglib.utils.usages import MagUsagesInfo, MagUsagesSetter, ResourceTypes


class TestInfo(TestCase):

    def test_img(self):
        m = Metadigit.from_xml_string(
            '<metadigit><img/></metadigit>'
        )
        info = MagUsagesInfo(m)
        master_img_type = ResourceTypes.MASTER_IMAGE_TYPE
        self.assertEqual(info.resource_types, [master_img_type])
        self.assertEqual(info.difform_resource_types, [])
        self.assertEqual(info.usages_map[master_img_type], [])

    def test_audio_proxies(self):
        m = Metadigit.from_xml_string(
            '<metadigit><audio> '
            '<proxies><usage>1</usage></proxies>'
            '<proxies><usage>2</usage><usage>b</usage></proxies>'
            '</audio></metadigit>')
        info = MagUsagesInfo(m)
        proxy_1_type = ResourceTypes.AUDIO_TYPES[0]
        proxy_2_type = ResourceTypes.AUDIO_TYPES[1]

        self.assertEqual(info.resource_types, [proxy_1_type, proxy_2_type])
        self.assertEqual(info.difform_resource_types, [])
        self.assertEqual(info.usages_map[proxy_1_type], ['1'])
        self.assertEqual(info.usages_map[proxy_2_type], ['2', 'b'])

    def test_difform(self):
        m = Metadigit.from_xml_string(
            '<metadigit>'
            '<img><usage>1</usage></img>'
            '<img><usage>2</usage></img>'
            '</metadigit>')

        info = MagUsagesInfo(m)
        master_img_type = ResourceTypes.MASTER_IMAGE_TYPE
        self.assertEqual(info.resource_types, [master_img_type])
        self.assertEqual(info.difform_resource_types, [master_img_type])
        self.assertEqual(info.usages_map[master_img_type], ['1', '2'])


class TestSet(TestCase):
    mag_1 = (
        '<metadigit>'
        '<img><altimg imggroupID="j1"/></img>'
        '<video><proxies/><proxies/></video>'
        '<video><proxies/><proxies/></video>'
        '<ocr><usage>1</usage></ocr>'
        '<ocr/>'
        '</metadigit>'
    )

    def setUp(self):
        self.m = Metadigit.from_xml_string(self.mag_1)
        self.setter = MagUsagesSetter(self.m)

    def test_img(self):
        self.setter.set(ResourceTypes.IMGGROUP_IMAGE_TYPES['tiff'], ('2', 'a'))
        self._assert_usages(self.m.img[0], [])

        self.setter.set(ResourceTypes.MASTER_IMAGE_TYPE, ('1', 'b'))
        self.setter.set(ResourceTypes.IMGGROUP_IMAGE_TYPES['j1'], ('2', 'a'))

        self._assert_usages(self.m.img[0], ['1', 'b'])
        self._assert_usages(self.m.img[0].altimg[0], ['2', 'a'])

    def test_video(self):
        self.setter.set(ResourceTypes.VIDEO_TYPES[0], ('1',))
        self._assert_usages(self.m.video[0].proxies[0], ['1'])
        self.setter.set(ResourceTypes.VIDEO_TYPES[1], ('2', 'b'))
        self._assert_usages(self.m.video[0].proxies[0], ['1'])
        self._assert_usages(self.m.video[0].proxies[1], ['2', 'b'])

    def test_ocr(self):
        self.setter.set(ResourceTypes.OCR_TYPE, [])
        self._assert_usages(self.m.ocr[0], [])
        self._assert_usages(self.m.ocr[1], [])
        self.setter.set(ResourceTypes.OCR_TYPE, ['2', '3'])
        self._assert_usages(self.m.ocr[0], ['2', '3'])
        self._assert_usages(self.m.ocr[1], ['2', '3'])


    def _assert_usages(self, resource, usages):
        self.assertEqual([u.value for u in resource.usage], usages)
