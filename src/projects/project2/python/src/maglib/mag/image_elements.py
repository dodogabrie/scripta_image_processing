#!/usr/bin/env python
# -*- coding: utf-8 -*-

from maglib.xmlbase import Attribute, Complex_element_instance, Element

from .core_elements import File


class Img(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        attributes = ( Attribute(name='imggroupID'),
                       Attribute(name='holdingsID') )
        elements = ( Element(name='sequence_number'),
                     Element(name='nomenclature'),
                     Element(name='usage', max_occurrences=None),
                     Element(name='side'),
                     Element(name='scale'),
                     Element(File, 'file'),
                     Element(name='md5'),
                     Element(name='filesize'),
                     Element(Dimensions, 'image_dimensions'),
                     Element(Metrics, 'image_metrics'),
                     Element(name='ppi'),         # deprecati
                     Element(name='dpi'),         #
                     Element(Format, 'format'),
                     Element(Scanning, 'scanning'),
                     Element(name='datetimecreated'),
                     Element(Target, 'target', max_occurrences=None),
                     Element(Altimg, 'altimg', max_occurrences=None),
                     Element(name='note') )

        super(Img, self).__init__(sub_elements=elements, attrs=attributes, name='img')

class Img_group(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        attributes = ( (Attribute(name='ID'),))
        elements = ( Element(Metrics, 'image_metrics'),
                     Element(name='ppi'),   # comunque deprecati
                     Element(name='dpi'),   #
                     Element(Format, 'format'),
                     Element(Scanning, 'scanning') )

        super(Img_group, self).__init__(
            sub_elements=elements, attrs=attributes, *args, **kwargs)

class Dimensions(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        elements = ( Element(name='imagelength', namespace='niso'),
                     Element(name='imagewidth', namespace='niso'),
                     Element(name='source_xdimension', namespace='niso'),
                     Element(name='source_ydimension', namespace='niso') )
        super(Dimensions, self).__init__(sub_elements=elements, *args, **kwargs)

class Metrics(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        elements = ( Element(name='samplingfrequencyunit', namespace='niso'),
                     Element(name='samplingfrequencyplane', namespace='niso'),
                     Element(name='xsamplingfrequency', namespace='niso'),
                     Element(name='ysamplingfrequency', namespace= 'niso'),
                     Element(name='photometricinterpretation', namespace='niso'),
                     Element(name='bitpersample', namespace='niso') )
        super(Metrics, self).__init__(sub_elements=elements, *args, **kwargs)

class Format(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        elements = ( Element(name='name', namespace='niso'),
                     Element(name='mime', namespace='niso'),
                     Element(name='compression', namespace='niso') )
        super(Format, self).__init__(sub_elements=elements, *args, **kwargs)

class Scanning(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        elements = ( Element(name='sourcetype', namespace='niso'),
                     Element(name='scanningagency', namespace='niso'),
                     Element(name='devicesource', namespace='niso'),
                     Element(Scanning_system, 'scanningsystem', 'niso') )
        super(Scanning, self).__init__(sub_elements=elements, *args, **kwargs)

class Scanning_system(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        elements = ( Element(name='scanner_manufacturer', namespace='niso'),
                     Element(name='scanner_model', namespace='niso'),
                     Element(name='capture_software', namespace='niso') )
        super(Scanning_system, self).__init__(sub_elements=elements, *args, **kwargs)


class Target(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        elements = ( Element(name='targetType', namespace='niso'),
                     Element(name='targetID', namespace='niso'),
                     Element(name='imageData', namespace='niso'),
                     Element(name='performanceData', namespace='niso'),
                     Element(name='profiles', namespace='niso') )
        super(Target, self).__init__(sub_elements=elements, *args, **kwargs)

class Altimg(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        attributes = ( Attribute(name='imggroupID'), )

        elements = ( Element(name='usage', max_occurrences=None),
                     Element(File, 'file'),
                     Element(name='md5'),
                     Element(name='filesize'),
                     Element(Dimensions, 'image_dimensions'),
                     Element(Metrics, 'image_metrics'),
                     Element(name='ppi'),  # deprecati
                     Element(name='dpi'),  #
                     Element(Format, 'format'),
                     Element(Scanning, 'scanning'),
                     Element(name='datetimecreated') )

        super(Altimg, self).__init__(sub_elements=elements, attrs=attributes, *args, **kwargs)
