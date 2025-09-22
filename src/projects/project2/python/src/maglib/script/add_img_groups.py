#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Importa gli img_group da un file ini in questa forma:

group0_id = tiff
group0_dpi = 600
group0_mimename = TIF
group0_mimetype = image/tiff
group0_compression = Uncompressed
group0_device = scanner
group0_manufacturer = i2s
group0_model = Digibook 10000 RGB
group0_software = Suprascan 10000 RGB

group1_id = jpeg300
group1_dpi = 300
group1_mimename = JPG
group1_mimetype = image/jpeg
group1_compression = JPG

group2_id = jpeg150
group2_dpi = 150
group2_mimename = JPG
group2_mimetype = image/jpeg
group2_compression = JPG
"""



from maglib.script.common import MagOperation, MagScriptMain, \
    MagScriptInfoFileOptParser, MagInfoReader, MagOperationError



class ImgGroupAdder(MagOperation):
    def __init__(self, img_groups_info_file):
        """:img_groups_info_file: file con le informazioni sugli img group
        da aggiungere"""
        self._info_file = img_groups_info_file

    def do_op(self, metadigit):
        if not metadigit.gen:
            metadigit.gen.add_instance()
        gen = metadigit.gen[0]

        img_groups_info = self._build_img_groups_info()

        for img_group_info in img_groups_info:
            group_id = img_group_info['id']
            img_group = self._get_or_create_img_group(gen.img_group, group_id)
            self._fill_img_group(img_group, img_group_info)

    def clean_mag(self, metadigit):
        if metadigit.gen:
            metadigit.gen[0].img_group.clear()

    def _build_img_groups_info(self):
        return ImgGroupsInfoReader.read_file(self._info_file)

    def _get_or_create_img_group(self, img_groups, group_id):
        for img_group in img_groups:
            if img_group.ID.value == group_id:
                return img_group
        img_groups.add_instance().ID.value = group_id
        return img_groups[-1]

    def _fill_img_group(self, img_group, img_group_info):
        if not img_group.image_metrics:
            img_group.image_metrics.add_instance()
        img_m = img_group.image_metrics[0]
        img_m.samplingfrequencyunit.set_value('2')
        img_m.samplingfrequencyplane.set_value('2')
        if img_group_info.get('dpi'):
            img_m.xsamplingfrequency.set_value(img_group_info['dpi'])
            img_m.ysamplingfrequency.set_value(img_group_info['dpi'])
        if img_group_info.get('photometricinterpretation'):
            img_m.photometricinterpretation.set_value(
                img_group_info.get('photometricinterpretation'))
        if img_group_info.get('bitpersample'):
            img_m.bitpersample.set_value(img_group_info.get('bitpersample'))
        if not img_group.format:
            img_group.format.add_instance()
        fmt = img_group.format[0]
        fmt.name.set_value(img_group_info['mimename'])
        fmt.mime.set_value(img_group_info['mimetype'])
        fmt.compression.set_value(img_group_info['compression'])

        if not img_group_info.get('device'):
            return
        if not img_group.scanning:
            img_group.scanning.add_instance()
        sc = img_group.scanning[0]
        if img_group_info.get('scanningagency'):
            sc.scanningagency.set_value(img_group_info['scanningagency'])
        sc.devicesource.set_value(img_group_info['device'])
        if not sc.scanningsystem:
            sc.scanningsystem.add_instance()
        sc_sys = sc.scanningsystem[0]
        if img_group_info.get('manufacturer'):
            sc_sys.scanner_manufacturer.set_value(img_group_info['manufacturer'])
        if img_group_info.get('model'):
            sc_sys.scanner_model.set_value(img_group_info['model'])
        if img_group_info.get('software'):
            sc_sys.capture_software.set_value(img_group_info['software'])



class Main(MagScriptMain):
    def _build_opt_parser(self):
        return MagScriptInfoFileOptParser(
            'file con le informazioni sugli img group da creare')

    def _build_mag_operation(self, opts, args):
        return ImgGroupAdder(opts.info_file)


class ImgGroupsInfoReader(MagInfoReader):
    @classmethod
    def read_file(self, fpath):
        readed = super(ImgGroupsInfoReader, self).read_file(fpath)
        groups = []

        c = 0
        while 1:
            if ('group%d_id' % c) in readed:
                prefix = 'group%d' % c
                group = {}
                group['id'] = readed[prefix+'_id']
                for attr in (
                    'dpi', 'mimename', 'mimetype', 'compression', 'device',
                    'scanningagency', 'manufacturer', 'model', 'software',
                    'photometricinterpretation', 'bitpersample'):
                    if (prefix + '_' + attr) in readed:
                        group[attr] = readed[prefix + '_' + attr]

                groups.append(group)
                c += 1
            else:
                break
        return groups

if __name__ == '__main__':
    import sys
    m = Main()
    sys.exit(m(sys.argv))
