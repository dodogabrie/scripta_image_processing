#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Questo modulo raccoglie alcuni elementi "transcription", raggruppati quà perché vengono usati sia
dagli elementi del gruppo video che da quelli del gruppo audio.
"""

from maglib.xmlbase import Element, Complex_element_instance, Simple_element_instance, Attribute

class Transcription_chain(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        elements = ( Element(Device_description, 'device_description'),
                     Element(name='device_manufacturer'),
                     Element(Device_model, 'device_model'),
                     Element(name='capture_software'),
                     Element(name='device_settings') )

        super(Transcription_chain, self).__init__(sub_elements=elements, *args, **kwargs)

class Transcription_summary(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        elements = ( Element(name='grouping'),
                     Element(Transcription_summary,
                             'transcriptionsummary', max_occurrences=None),
                     Element(name='data_description'),
                     Element(name='data_unit'),
                     Element(name='data_value') )

        super(Transcription_summary, self).__init__(sub_elements=elements, *args, **kwargs)

class Transcription_data(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        elements = ( Element(name='grouping'),
                     Element(Transcription_data,
                             'transcriptiondata', max_occurrences=None),
                     Element(name='data_description'),
                     Element(name='data_unit'),
                     Element(Interval, 'interval'),
                     Element(name='data_value', max_occurrences=None) )

        super(Transcription_data, self).__init__(sub_elements=elements, *args, **kwargs)

class Device_description(Simple_element_instance):
    def __init__(self, *args, **kwargs):
        attributes = ( Attribute(name='Type'),
                       Attribute(name='Unique_identifier'),
                       Attribute('Comments') )
        super(Device_description, self).__init__(attrs=attributes, *args, **kwargs)

class Device_model(Simple_element_instance):
    def __init__(self, *args, **kwargs):
        attributes = ( Attribute(name='Model'),
                       Attribute(name='Serial_number') )
        super(Device_model, self).__init__(attrs=attributes, *args, **kwargs)

class Interval(Simple_element_instance):
    def __init__(self, *args, **kwargs):
        attributes = ( Attribute(name='start'),
                       Attribute(name='stop') )
        super(Interval, self).__init__(attrs=attributes, *args, **kwargs)
