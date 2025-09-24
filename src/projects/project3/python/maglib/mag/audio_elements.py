#! /usr/bin/env python
# -*- coding: utf-8 -*-
from maglib.xmlbase import Attribute, Complex_element_instance, Element

from . import transcription_elements
from .core_elements import File


class Audio(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        attributes = ( Attribute(name='holdingsID'),
                       Attribute(name='audiogroupID') )

        elements = ( Element(name='sequence_number'),
                     Element(name='nomenclature'),
                     Element(Proxies, 'proxies', max_occurrences=None),
                     Element(name='note') )
        super(Audio, self).__init__(sub_elements=elements, attrs=attributes, *args, **kwargs)


class Audio_group(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        attributes = ( Attribute(name='ID'), )
        elements = ( Element(Metrics, 'audio_metrics'),
                     Element(Format, 'format'),
                     Element(Transcription, 'transcription') )
        super(Audio_group, self).__init__(sub_elements=elements, attrs=attributes, *args, **kwargs)


class Metrics(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        elements = ( Element(name='samplingfrequency'),
                     Element(name='bitpersample'),
                     Element(name='bitrate') )
        super(Metrics, self).__init__(sub_elements=elements, *args, **kwargs)

class Format(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        elements = ( Element(name='name'),
                     Element(name='mime'),
                     Element(name='compression'),
                     Element(name='channel_configuration') )

        super(Format, self).__init__(sub_elements=elements, *args, **kwargs)

class Transcription(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        elements = ( Element(name='sourcetype'),
                     Element(name='transcriptionagency'),
                     Element(name='transcriptiondate'),
                     Element(name='devicesource'),
                     Element(transcription_elements.Transcription_chain,
                             'transcriptionchain', max_occurrences=None),
                     Element(transcription_elements.Transcription_summary,
                             'transcriptionsummary', max_occurrences=None),
                     Element(transcription_elements.Transcription_data,
                             'transcriptiondata', max_occurrences=None) )
        super(Transcription, self).__init__(sub_elements=elements, *args, **kwargs)

class Dimensions(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        super(Dimensions, self).__init__(
            sub_elements=( Element(name='duration'), ), *args, **kwargs)

class Proxies(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        attributes = ( Attribute(name='audiogroupID'), )
        elements = ( Element(name='usage', max_occurrences=None),
                     Element(File, 'file'),
                     Element(name='md5'),
                     Element(name='filesize'),
                     Element(Dimensions, 'audio_dimensions'),
                     Element(Metrics, 'audio_metrics'),
                     Element(Format, 'format'),
                     Element(Transcription, 'transcription'),
                     Element(name='datetimecreated') )
        super(Proxies, self).__init__(sub_elements=elements, attrs=attributes, *args, **kwargs)
