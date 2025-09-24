#! /usr/bin/env python
# -*- coding: utf-8 -*-

from maglib.xmlbase import (
    Attribute,
    Complex_element_instance,
    Element,
    Simple_element_instance,
)

from .core_elements import Dc_element_with_lang


class Contlet(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        elements = ( Element(name='identifier', namespace='dc', max_occurrences=None),
                     Element(Dc_element_with_lang, 'title', 'dc', max_occurrences=None),
                     Element(name='creator', namespace='dc', max_occurrences=None),
                     Element(name='publisher', namespace='dc', max_occurrences=None),
                     Element(Dc_element_with_lang, 'subject', 'dc', max_occurrences=None),
                     Element(Dc_element_with_lang, 'description',
                             'dc', max_occurrences=None),
                     Element(name='contributor', namespace='dc', max_occurrences=None),
                     Element(name='date', namespace='dc', max_occurrences=None),
                     Element(Dc_element_with_lang, 'type', 'dc', max_occurrences=None),
                     Element(Dc_element_with_lang, 'format', 'dc', max_occurrences=None),
                     Element(Dc_element_with_lang, 'source', 'dc', max_occurrences=None),
                     Element(name='language', namespace='dc', max_occurrences=None),
                     Element(name='relation', namespace='dc', max_occurrences=None),
                     Element(name='coverage', namespace='dc', max_occurrences=None),
                     Element(name='rights', namespace='dc', max_occurrences=None),

                     Element(name='replacedBy'),
                     Element(Geographic_link, 'geographic_link',max_occurrences=None),
                     Element(Ontologic_link, 'ontologic_link', max_occurrences=None),
                     Element(Resource, 'resource', max_occurrences=None) )
        super(Contlet, self).__init__(sub_elements=elements, *args, **kwargs)


class Geographic_link(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        elements = ( Element(name='relation', max_occurrences=None),
                     Element(Geographic_position, 'position') )

        super(Geographic_link, self).__init__(sub_elements=elements, *args, **kwargs)

class Geographic_position(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        elements = ( Element(Geographic_radius, 'radius'),
                     Element(Geographic_point, 'point') )

        super(Geographic_position, self).__init__(sub_elements=elements, *args, **kwargs)

class Geographic_radius(Simple_element_instance):
    def __init__(self, *args, **kwargs):
        super(Geographic_radius, self).__init__(attrs=(Attribute(name='unit'),), *args, **kwargs)

class Geographic_point(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        elements = ( Element(name='latitude'),
                     Element(name='longitude') )
        super(Geographic_point, self).__init__(sub_elements=elements, *args, **kwargs)

class Ontologic_link(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        elements = ( Element(name='ontology'),
                     Element(Ontology_instance, 'instance'),
                     Element(name='matching') )

        super(Ontologic_link, self).__init__(sub_elements=elements, *args, **kwargs)

class Ontology_instance(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        elements = ( Element(name='base_instance'),
                     Element(Ontology_property, 'property', max_occurrences=None) )
        super(Ontology_instance, self).__init__(sub_elements=elements, *args, **kwargs)

class Ontology_property(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        elements = ( Element(name='predicate'),
                     Element(name='object') )
        super(Ontology_property, self).__init__(sub_elements=element, *args, **kwargs)

class Resource(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        elements = ( Element(name='location'),
                     Element(Img_element, 'img_element'),
                     Element(Video_element, 'video_element'),
                     Element(Doc_element, 'doc_element'),
                     Element(Doc_element, 'ocr_element'),
                     Element(Audio_element, 'audio_element'),
                     Element(name='semantic_element') )
        super(Resource, self).__init__(sub_elements=elements, *args, **kwargs)

class Img_element(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        elements = ( Element(Sequence_numbers, 'sequence_numbers'),
                     Element(Img_section, 'img_section') )
        super(Img_element, self).__init__(sub_elements=elements, *args, **kwargs)

class Img_section(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        elements = ( Element(Point, 'point', max_occurrences=None) )
        super(Img_section, self).__init__(sub_elements=elements, *args, **kwargs)

class Point(Complex_element_instance):
    def __init__(self):
        elements = ( Element(name='horizontal_position'),
                     Element(name='vertical_position') )
        super(Point, self).__init__(sub_elements=elements, *args, **kwargs)


class Video_element(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        elements = ( Element(Sequence_numbers, 'sequence_numbers'),
                     Element(Video_section, 'video-section') )
        super(Video_element, self).__init__(sub_elements=elements, *args, **kwargs)

class Video_section(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        elements = ( Element(Img_section, 'spatial_section'),
                    Element(Temporal_section, 'temporal_section') )
        super(Video_section, self).__init__(sub_elements=elements, *args, **kwargs)

class Doc_element(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        elements = ( Element(Sequence_numbers, 'sequence_numbers'),
                     Element(Doc_section, 'doc_section') )
        super(Doc_element, self).__init__(sub_elements=element, *args, **kwargs)

class Doc_section(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        elements = ( Element(name='start_character'),
                     Element(name='end_character') )

        super(Doc_section, self).__init__(sub_elements=elements, *args, **kwargs)

class Audio_element(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        elements = ( Element(Sequence_numbers, 'sequence_numbers'),
                     Element(Temporal_section, 'audio_section') )
        super(Audio_element, self).__init__(sub_elements=elements, *args, **kwargs)

class Temporal_section(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        elements = ( Element(name='start'),
                     Element(name='end') )

        super(Temporal_section, self).__init__(sub_elements=elements, *args, **kwargs)


class Sequence_numbers(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        elements = ( Element(name='sequence_number', max_occurrences=None),
                     Element(Sequence_interval, 'sequence_interval', max_occurrences=None) )

        super(Sequence_numbers, self).__init__(sub_elements=elements, *args, **kwargs)

class Sequence_interval(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        elements = ( Element(name='start_sequence_number'),
                     Element(name='stop_sequence_number') )
        super(Sequence_interval, self).__init__(sub_elements=elements, *args, **kwargs)
