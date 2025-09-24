#! /usr/bin/env python
# -*- coding: utf-8 -*-
from maglib.xmlbase import Attribute, Complex_element_instance, Element

from . import transcription_elements
from .core_elements import File


class Video(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        attributes = (
            Attribute(name='holdingsID'),
            Attribute(name='videogroupID'),
        )

        elements = ( Element(name='sequence_number'),
                     Element(name='nomenclature'),
                     Element(Proxies, 'proxies', max_occurrences=None),
                     Element(name='note') )

        super(Video, self).__init__(sub_elements=elements, attrs=attributes, *args, **kwargs)


class Video_group(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        attributes = ( Attribute(name='ID') )
        elements = ( Element(Metrics, 'video_metrics'),
                     Element(Format, 'format'),
                     Element(Digitisation, 'digitisation') )
        super(Video_group, self).__init__(
            sub_elements=elements, attrs=attributes, *args, **kwargs)

class Metrics(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        elements = ( Element(name='videosize'),
                     Element(name='aspectratio'),
                     Element(name='framerate') )
        super(Metrics, self).__init__(sub_elements=elements, *args, **kwargs)

class Format(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        elements = ( Element(name='name'),
                     Element(name='mime'),
                     Element(name='videoformat'),
                     Element(name='encode'),
                     Element(name='streamtype'),
                     Element(name='codec') )
        super(Format, self).__init__(sub_elements=elements, *args, **kwargs)

class Digitisation(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        elements = ( Element(name='sourcetype'),
                     Element(name='transcriptionagency'),
                     Element(name='devicesource'),
                     Element(transcription_elements.Transcription_chain, max_occurrences=None),
                     Element(transcription_elements.Transcription_summary, max_occurrences=None),
                     Element(transcription_elements.Transcription_data, max_occurrences=None) )
        super(Digitisation, self).__init__(
                sub_elements=elements, *args, **kwargs)

class Dimensions(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        super(Dimensions, self).__init__(sub_elements=( Element(name='duration'), ),
                                         *args, **kwargs)


class Proxies(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        attributes = (Attribute(name='videogroupID'), )
        elements = ( Element(name='usage', max_occurrences=None),
                     Element(File, 'file'),
                     Element(name='md5'),
                     Element(name='filesize'),
                     Element(Dimensions, 'video_dimensions'),
                     Element(Metrics, 'video_metrics'),
                     Element(Format, 'format'),
                     Element(Digitisation, 'digitisation'),
                     Element(name='datetimecreated') )

        super(Proxies, self).__init__(sub_elements=elements, attrs=attributes,
                                      *args, **kwargs)
