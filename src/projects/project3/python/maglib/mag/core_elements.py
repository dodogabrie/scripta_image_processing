from maglib.xmlbase import (
    Attribute,
    Complex_element_instance,
    Simple_element_instance,
)


class File(Complex_element_instance):
    def __init__(self, *args, **kwargs):
        # link deriva da xlink:simpleLink, e in quanto tale ha una
        # miriade di attributi
        attributes = (
            Attribute(name='href', namespace='xlink'),
            Attribute(name='role', namespace='xlink'),
            Attribute(name='arcrole', namespace='xlink'),
            Attribute(name='title', namespace='xlink'),
            Attribute(name='show', namespace='xlink'),
            Attribute(name='actuate', namespace='xlink'),
            Attribute(name='type', namespace='xlink'),
            Attribute(name='Location'),
        )
        super(File, self).__init__(attrs=attributes, *args, **kwargs)


class Dc_element_with_lang(Simple_element_instance):
    def __init__(self, *args, **kwargs):
        super(Dc_element_with_lang, self).__init__(
            attrs=(Attribute(name='lang', namespace='xml'),), *args, **kwargs)
