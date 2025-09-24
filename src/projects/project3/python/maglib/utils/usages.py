# -*- coding: utf-8 -*-


"""
questo modulo contiene strumenti per conoscere e modificare gli usage
delle risorse del mag in modo massivo

>>> from maglib import Metadigit
>>> mag = Metadigit('mymag.xml')
>>> usage_setter = MagUsagesSetter(mag)
>>> # imposta [1] come usages per le immagini che hanno imggroup tiff
>>> usage_setter.set(ResourceTypes.IMGGROUP_IMAGE_TYPES['tiff'], ('1',))
>>> # imposta [1, b] come usages per le immagini master che NON hanno imggroup
>>> usage_setter.set(ResourceTypes.MASTER_IMAGE_TYPE, ('1', 'b'))
>>> # imposta [2, a] come usages per tutti i doc
>>> usage_setter.set(ResourceTypes.DOC_TYPE, ('2', 'a'))
>>> # imposta [3] come usages per i secondi proxy video del mag
>>> usage_setter.set(ResourceTypes.VIDEO_TYPES[1], ('2', 'a'))
"""


from maglib.utils import mag_wrapper


class AutoFillList(list):
    """una lista che quando interrogata per un elemento che non possiede
    si riempe fino a quell'indice con oggetti creati con una certa classe
    e passando l'indice al costruttore"""

    def __getitem__(self, index):
        while index >= len(self):
            self.append(self._object_class(len(self)))
        return super(AutoFillList, self).__getitem__(index)

    @property
    def _object_class(self):
        raise NotImplementedError()


class ResourceType(object):
    """la tipologia a cui può appartenere una risorsa"""

    def __str__(self):
        raise NotImplementedError()

    def __eq__(self):
        raise NotImplementedError()


class ImageType(ResourceType):
    """una tipologia di immagine"""


class ImgGroupImageType(ImageType):
    """una tipologia di immagini che si contraddistinguono nell' appartenere
    allo stesso gruppo di immagini"""

    def __init__(self, img_group_name):
        self._img_group_name = img_group_name

    @property
    def img_group_name(self):
        return self._img_group_name

    def __str__(self):
        return self._img_group_name

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__)
            and self._img_group_name == other._img_group_name
        )

    def __hash__(self):
        return hash((self.__class__, self._img_group_name))


class ImgGroupImageTypes(dict):
    """contenitore per ImgGroupImageType"""

    def __getitem__(self, key):
        if key not in self:
            self[key] = ImgGroupImageType(key)
        return super(ImgGroupImageTypes, self).__getitem__(key)


class AltImageType(ImageType):
    """una tipologia per le immagini che sono formati alternativi
    con un certo indice"""

    def __init__(self, altimg_index):
        self._index = altimg_index

    def __str__(self):
        return "immagini alternative %d" % (self._index + 1)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self._index == other._index

    def __hash__(self):
        return hash((self.__class__, self._index))


class AltImageTypes(AutoFillList):
    """contenitore per AltImageType"""

    _object_class = AltImageType


class MasterImageType(ImageType):
    def __str__(self):
        return "immagini master"

    def __eq__(self, other):
        return isinstance(other, self.__class__)

    def __hash__(self):
        return hash(MasterImageType)


class DocType(ResourceType):
    """tipologia per un doc"""

    def __str__(self):
        return "doc"

    def __eq__(self, other):
        return isinstance(other, self.__class__)

    def __hash__(self):
        return hash(DocType)


class OcrType(ResourceType):
    """tipologia per un ocr"""

    def __str__(self):
        return "ocr"

    def __eq__(self, other):
        return isinstance(other, self.__class__)

    def __hash__(self):
        return hash(OcrType)


class AudioType(ResourceType):
    """tipologia per un audio, identificata dalla posizione dell'audio
    come proxy"""

    def __init__(self, proxy_index):
        self._proxy_index = proxy_index

    @property
    def proxy_index(self):
        return self._proxy_index

    def __str__(self):
        return "audio - proxy %d" % (self._proxy_index + 1)

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__)
            and self._proxy_index == other._proxy_index
        )

    def __hash__(self):
        return hash(self._proxy_index)


class AudioTypes(AutoFillList):
    """contenitore per AudioType"""

    _object_class = AudioType


class VideoType(ResourceType):
    """tipologia per un video, identificata dalla posizione
    del video come proxy"""

    def __init__(self, proxy_index):
        self._proxy_index = proxy_index

    @property
    def proxy_index(self):
        return self._proxy_index

    def __str__(self):
        return "video - proxy %d" % (self._proxy_index + 1)

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__)
            and self._proxy_index == other._proxy_index
        )

    def __hash__(self):
        return hash(self._proxy_index)


class VideoTypes(AutoFillList):
    """contenitore per VideoType"""

    _object_class = VideoType


class ResourceTypes(object):
    """tipo di risorsa può essere una stringa o una costante di questa classe"""

    MASTER_IMAGE_TYPE = MasterImageType()
    ALT_IMAGE_TYPES = AltImageTypes()
    IMGGROUP_IMAGE_TYPES = ImgGroupImageTypes()
    AUDIO_TYPES = AudioTypes()
    VIDEO_TYPES = VideoTypes()
    DOC_TYPE = DocType()
    OCR_TYPE = OcrType()

    @classmethod
    def type_for_image(cls, img, altimg_index):
        """ottiene il tipo per l'immagine.
        :param img: nodo img del mag
        :param int altimg_index: indice dell'altimg se è un'immagine,
               altrimenti se è master -1
        :return: il tipo per l'immagine
        :rtype: ImageType"""
        if img.imggroupID.value:
            return cls.IMGGROUP_IMAGE_TYPES[img.imggroupID.value]
        if altimg_index < 0:
            return cls.MASTER_IMAGE_TYPE
        return cls.ALT_IMAGE_TYPES[altimg_index]

    @classmethod
    def type_for_audio_proxy(cls, audio_proxy, proxy_index):
        """ottiene il tipo per un nodo audio proxy del mag
        :param audio_proxy: nodo proxy audio del mag
        :param int proxy_index: indice del proxy nel nodo audio
        :return: il tipo per il proxy audio
        :rtype: AudioType"""
        return cls.AUDIO_TYPES[proxy_index]

    @classmethod
    def type_for_video_proxy(cls, video_proxy, proxy_index):
        """ottiene il tipo per un nodo video proxy del mag
        :param video_proxy: nodo proxy video del mag
        :param int proxy_index: indice del proxy nell'elemento video
        :return: il tipo per il proxy video
        :rtype: VideoType"""
        return cls.VIDEO_TYPES[proxy_index]

    @classmethod
    def type_for_doc(cls, doc):
        """ottiene il tipo per un nodo doc del mag
        :param doc: nodo doc del amg
        :return: il tipo per il doc
        :rtype: DocType"""
        return cls.DOC_TYPE

    @classmethod
    def type_for_ocr(cls, ocr):
        """ottiene il tipo per un nodo ocr del mag
        :param ocr: nodo ocr del amg
        :return: il tipo per il ocr
        :rtype: OcrType"""
        return cls.OCR_TYPE


class MagUsagesInfo(object):
    """raccoglie le informazioni sugli usage delle risorse di un mag"""

    def __init__(self, metadigit):
        self._metadigit = metadigit
        self._usages_map = {}
        self._resource_types = []
        self._difform_resources_types = []
        self._compute_info()

    @property
    def usages_map(self):
        """dizionario con la mappatura tipo di risorsa -> lista usage"""

        return self._usages_map

    @property
    def resource_types(self):
        """lista di tipi di risorse del mag"""
        return self._resource_types

    @property
    def difform_resource_types(self):
        """lista con i tipi che hanno usage difformi nelle loro risorse"""
        return self._difform_resources_types

    def _compute_info(self):
        # scorro con indice a partire da -1 in modo da passare il parametro
        # corretto a ImageTypes.type_for_image
        for img_node in self._metadigit.img:
            for i, img in enumerate([img_node] + list(img_node.altimg), -1):
                resource_type = ResourceTypes.type_for_image(img, i)
                self._update_info_for_resource(img, resource_type)

        for ocr in self._metadigit.ocr:
            self._update_info_for_resource(ocr, ResourceTypes.type_for_ocr(ocr))
        for doc in self._metadigit.doc:
            self._update_info_for_resource(doc, ResourceTypes.type_for_doc(doc))

        for audio in self._metadigit.audio:
            for i, proxies in enumerate(audio.proxies):
                resource_type = ResourceTypes.type_for_audio_proxy(proxies, i)
                self._update_info_for_resource(proxies, resource_type)
        for video in self._metadigit.video:
            for i, proxies in enumerate(video.proxies):
                resource_type = ResourceTypes.type_for_video_proxy(proxies, i)
                self._update_info_for_resource(proxies, resource_type)

    def _update_info_for_resource(self, resource, resource_type):
        usages = mag_wrapper.get_resource_usages(resource)
        if resource_type not in self._resource_types:
            self._resource_types.append(resource_type)
            self._usages_map[resource_type] = usages
        else:
            if set(usages) != set(self._usages_map[resource_type]):
                if not resource_type in self._difform_resources_types:
                    self._difform_resources_types.append(resource_type)
                for usage in usages:
                    if not usage in self._usages_map[resource_type]:
                        self._usages_map[resource_type].append(usage)


class MagUsagesSetter(object):
    """imposta gli usage in un mag"""

    def __init__(self, metadigit):
        self._metadigit = metadigit

    def set(self, resource_type, usages):
        """imposta gli usage per un certo tipo di risorse
        :param ResourceType resource_type: tipo delle risorse da impostare
        :param list[str] usages: lista di usages da inserire"""
        types_methods = (
            (ImageType, self._set_img),
            (DocType, self._set_doc),
            (OcrType, self._set_ocr),
            (AudioType, self._set_audio),
            (VideoType, self._set_video),
        )
        for type_, method in types_methods:
            if isinstance(resource_type, type_):
                method(resource_type, usages)
                break
        else:
            raise RuntimeError("unknown resource type %s" % resource_type)

    def _set_doc(self, resource_type, usages):
        for doc in self._metadigit.doc:
            self._set_on_resource(doc, usages)

    def _set_ocr(self, resource_type, usages):
        for ocr in self._metadigit.ocr:
            self._set_on_resource(ocr, usages)

    def _set_img(self, resource_type, usages):
        for img_node in self._metadigit.img:
            for i, img in enumerate([img_node] + list(img_node.altimg), -1):
                img_type = ResourceTypes.type_for_image(img, i)
                if img_type == resource_type:
                    self._set_on_resource(img, usages)

    def _set_audio(self, resource_type, usages):
        proxy_index = resource_type.proxy_index
        for audio in self._metadigit.audio:
            if len(audio.proxies) > proxy_index:
                self._set_on_resource(audio.proxies[proxy_index], usages)

    def _set_video(self, resource_type, usages):
        proxy_index = resource_type.proxy_index
        for video in self._metadigit.video:
            if len(video.proxies) > proxy_index:
                self._set_on_resource(video.proxies[proxy_index], usages)

    def _set_on_resource(self, resource, usages):
        # imposta una singola risorsa
        resource.usage.clear()
        for usage in usages:
            resource.usage.add_instance().value = usage
