import os

from maglib.mag.audio_elements import Audio
from maglib.mag.video_elements import Video
from maglib.utils.stru_mag_wrapper import StruSeqNFix


# FUNZIONI SULLE LISTE DI RISORSE
class ResourcesSort:
    """ordina un tipo di risorse del mag"""

    def __init__(self, rsrcs_node):
        """:rsrcs_node: nodo con le risorse da ordinare"""
        self._rsrcs_node = rsrcs_node

    def sort_by_filename(self):
        """ordina le risorse in base al nome del file"""
        self._rsrcs_node.sort(key=self._get_resource_filename)

    def _get_resource_filename(self, rsrc):
        raise NotImplementedError()


class ImagesSort(ResourcesSort):
    """ordina le immagini del mag"""

    def _get_resource_filename(self, rsrc):
        if rsrc.file and rsrc.file[0].href.value:
            return os.path.basename(rsrc.file[0].href.value)
        return ""


"""ordina i doc del mag"""
DocsSort = ImagesSort

""" ordina gli ocr del mag"""
OcrSort = DocsSort


class ProxiedResourceSort(ResourcesSort):
    """ordina una risorsa "proxied" (audio vide) del mag"""

    def _get_resource_filename(self, resource):
        if not resource.proxies:
            return ""
        proxy = resource.proxies[0]
        if proxy.file and proxy.file[0].href.value:
            return os.path.basename(proxy.file[0].href.value)
        return ""


class AudioSort(ProxiedResourceSort):
    """ordina gli audio del mag"""


class VideoSort(ProxiedResourceSort):
    """ordina i video del mag"""


class SeqNsReset:
    """riassegna i seq_n alle risorse del mag in modo sequenziale,
    preservando i collegamenti nella stru"""

    @classmethod
    def on_mag(cls, metadigit, resources=("img", "doc")):
        """reimposta il seq_n su tutte le risorse del mag
        :metadigit: mag su cui operare
        :resources: risorse su cui operare"""
        for rsrc in resources:
            rsrc_node = getattr(metadigit, rsrc)
            cls.on_resource_node(rsrc_node, rsrc, metadigit.stru)

    @classmethod
    def on_resource_node(cls, resource_node, node_name, stru_node):
        """reimposta il seq_n per un nodo di risorse
        :resources_node: nodo di risorse
        :node_name: nodo del nome di risorse"""
        stru_fix = StruSeqNFix(stru_node, node_name)
        cls.on_node(resource_node, stru_fix)

    @classmethod
    def on_node(cls, node, stru_fix=None, start=1):
        """effettua il reset su una serie di elementi.
        se stru_fix non è None preserva i collegamenti nella stru
        :stru_fux: StruSeqNFix per preservare i collegamenti nella stru
        :start: primo sequence_number"""
        if not stru_fix:
            for i, resource in enumerate(node, start):
                resource.sequence_number.set_value(str(i))
        else:
            seq_n_map = {}
            for i, resource in enumerate(node, start):
                try:
                    old_seq_n = int(resource.sequence_number.get_value())
                except (TypeError, ValueError):
                    old_seq_n = None
                if old_seq_n:
                    seq_n_map[int(old_seq_n)] = i
                resource.sequence_number.set_value(str(i))
            stru_fix.fix(seq_n_map)


class IndexesForSeqN:
    """converte un intervallo di seq_n start-stop nella lista di indici
    delle risorse interessate relativa del nodo di risorse"""

    def __init__(self, rsrcs_node, start, stop):
        """":rsrcs_node: nodo con le risorse
        :start: :stop: range di sequence_number"""
        self._rsrcs_node = rsrcs_node
        self._start = int(start)
        self._stop = int(stop)
        self._indexes = None

    @property
    def indexes(self):
        """la lista di indici delle risorse il cui seq_n è compreso
        in start:stop"""
        if self._indexes is None:
            self._indexes = self._compute_indexes()
        return self._indexes

    def _compute_indexes(self):
        indexes = []
        for i, rsrc in enumerate(self._rsrcs_node):
            rsrc_seq_n = rsrc.sequence_number.get_value()
            if rsrc_seq_n:
                rsrc_seq_n = int(rsrc_seq_n)
                if rsrc_seq_n >= self._start and rsrc_seq_n <= self._stop:
                    indexes.append(i)
        return indexes


# FUNZIONI SULLE RISORSE
# per risorse si intende img, altimg, ocr, doc, o un proxy audio o video


def get_resource_sequence_number(resource):
    """ritorna il sequence_number della risorsa, oppure la stringa
    vuota se non ce l'ha"""
    # ogni tipo di risorsa tiene il sequence number nello stesso modo
    if (not resource.sequence_number) or (not resource.sequence_number[0].value):
        return ""
    else:
        return resource.sequence_number[0].value


def set_resource_sequence_number(resource, new_sequence_number):
    """modifica il sequence_number di un nodo risorsa"""
    new_sequence_number = str(new_sequence_number)
    if not resource.sequence_number:
        resource.sequence_number.add_instance()
    resource.sequence_number[0].value = new_sequence_number


def get_resource_basename(resource):
    """ritorna il nome base del file principale legato alla risorsa, vale a dire
    il nome del file senza path e senza estensione. Se il file non è
    specificato ritorna la stringa vuota."""
    if not resource.file or not resource.file[0].href.value:
        return ""
    filepath = resource.file[0].href.value
    filename = os.path.basename(filepath)
    return os.path.splitext(filename)[0]


def resource_is_proxied(resource):
    # dice se una risorsa è di tipo proxy, vale a dire se tiene le informazioni
    # sul file non direttamente in se stessa ma all'interno dei un sottoelemento proxies
    return isinstance(resource, (Video, Audio))


def get_all_resource_basename(resource):
    """ritorna il nome base del file principale legato alla risorsa, vale a dire
    il nome del file senza path e senza estensione. Se il file non è
    specificato ritorna la stringa vuota
    funziona su tutti i tipi di risorse."""
    if resource_is_proxied(resource):
        if not resource.proxies:
            return ""
        return get_resource_basename(resource.proxies[0])
    return get_resource_basename(resource)


def get_resource_filepath(resource):
    """ritorna il path del file di una risorsa, o la stringa vuota se non
    è presente"""
    if not resource.file or not resource.file[0].href.value:
        return ""
    return resource.file[0].href.value


def get_all_resource_filepath(resource):
    """ritorna il path del file di una risorsa, o la stringa vuota se non è
    presente. funziona anche sui tipi con proxies"""
    if resource_is_proxied(resource):
        if not resource.proxies:
            return ""
        return get_resource_filepath(resource.proxies[0])
    return get_resource_filepath(resource)


def set_resource_filepath(resource, filepath):
    """imposta il filepath per una risorsa"""
    if not resource.file:
        resource.file.add_instance()
    resource.file[0].Location.value = "URI"
    resource.file[0].href.value = filepath


def get_resource_usage(resource):
    """ritorna l'usage per una risorsa o ''"""
    if not resource.usage:
        return ""
    return resource.usage[0].value


def get_resource_usages(resource):
    """ritorna la lista di usages espressi da una risorsa"""
    return [u.value for u in resource.usage]


def set_resource_usage(resource, usage):
    """imposta l'usage per una risorsa"""
    if not resource.usage:
        resource.usage.add_instance()
    resource.usage[0].value = usage


def add_resource_usage(resource, usage):
    """aggiunge un nuovo usage per una risorsa"""
    resource.usage.add_instance().value = usage


def get_resource_nomenclature(resource):
    """ritorna la nomenclatura della risorsa,
    oppure la stringa vuota se essa non è specificata"""
    if not resource.nomenclature or not resource.nomenclature[0].value:
        return ""
    else:
        return resource.nomenclature[0].value


def set_resource_nomenclature(resource, new_nomenclature):
    """imposta la nuova nomenclatura new_nomenclature per la risorsa resource"""
    if not resource.nomenclature:
        resource.nomenclature.add_instance()
    resource.nomenclature[0].value = new_nomenclature


def get_resource_md5(resource):
    """ritorna l'md5 per una risorsa, oppure la tringa vuota se esso non è
    presente"""
    if not resource.md5 or not resource.md5[0].value:
        return ""
    return resource.md5[0].value


def set_resource_md5(resource, md5):
    """imposta un nuovo hash md5 per la risorsa resource"""
    if not resource.md5:
        resource.md5.add_instance()
    resource.md5[0].value = md5


def set_resource_filesize(resource, filesize):
    """imposta un nuovo filesize per la risorsa resource"""
    if not resource.filesize:
        resource.filesize.add_instance()
    resource.filesize[0].value = filesize


def get_resource_format_name(resource):
    """ritorna il nome del formato di una risorsa
    PS: funziona anche sugli img_group"""
    if not resource.format or not resource.format[0].name:
        return ""
    return resource.format[0].name[0].value


def get_resource_format_mimetype(resource):
    """ritorna il mimetype del formato di una risorsa
    PS: funziona anche sugli img_group"""
    if not resource.format or not resource.format[0].mime:
        return ""
    return resource.format[0].mime[0].value


def get_resource_format_compression(resource):
    """ritorna la compressione del formato di una risorsa
    PS: funziona anche sugli img_group"""
    if not resource.format or not resource.format[0].compression:
        return ""
    return resource.format[0].compression[0].value


def set_resource_format_name(resource, format_name):
    """imposta un nuovo nome del formato per la risorsa resource"""
    if not resource.format:
        resource.format.add_instance()
    if not resource.format[0].name:
        resource.format[0].name.add_instance()
    resource.format[0].name[0].value = format_name


def set_resource_format_mimetype(resource, mimetype):
    if not resource.format:
        resource.format.add_instance()
    if not resource.format[0].mime:
        resource.format[0].mime.add_instance()
    resource.format[0].mime[0].value = mimetype


def set_resource_format_compression(resource, compression):
    if not resource.format:
        resource.format.add_instance()
    if not resource.format[0].compression:
        resource.format[0].compression.add_instance()
    resource.format[0].compression[0].value = compression


def set_resource_datetimecreated(resource, datetimecreated):
    if not resource.datetimecreated:
        resource.datetimecreated.add_instance()
    resource.datetimecreated[0].value = datetimecreated


# FUNZIONI SULLE IMMAGINI
# funzionano anche sulle altimg
def set_img_length(img_node, length):
    """
    imposta la lunghezza dell'immagine
    """
    if not img_node.image_dimensions:
        img_node.image_dimensions.add_instance()
    if not img_node.image_dimensions[0].imagelength:
        img_node.image_dimensions[0].imagelength.add_instance()
    img_node.image_dimensions[0].imagelength[0].value = length


def set_img_width(img_node, width):
    """
    imposta la larghezza dell'immagine
    """
    if not img_node.image_dimensions:
        img_node.image_dimensions.add_instance()
    if not img_node.image_dimensions[0].imagewidth:
        img_node.image_dimensions[0].imagewidth.add_instance()
    img_node.image_dimensions[0].imagewidth[0].value = width


def get_img_samplingfrequencyunit(img_node):
    """
    ritorna il samplingfrequencyunit del'immagine o dell'imggroup
    """
    if (
        (not img_node.image_metrics)
        or (not img_node.image_metrics[0].samplingfrequencyunit)
        or (not img_node.image_metrics[0].samplingfrequencyunit[0].value)
    ):
        return ""
    else:
        return img_node.image_metrics[0].samplingfrequencyunit[0].value


def set_img_samplingfrequencyunit(img_node, samplingfrequencyunit):
    """
    imposta il samplingfrequencyunit per l'immagine
    """
    if not img_node.image_metrics:
        img_node.image_metrics.add_instance()
    if not img_node.image_metrics[0].samplingfrequencyunit:
        img_node.image_metrics[0].samplingfrequencyunit.add_instance()
    img_node.image_metrics[0].samplingfrequencyunit[0].value = samplingfrequencyunit


def get_img_samplingfrequencyplane(img_node):
    """
    ritorna il samplingfrequencyplane del'immagine o dell'imggroup
    """
    if (
        (not img_node.image_metrics)
        or (not img_node.image_metrics[0].samplingfrequencyplane)
        or (not img_node.image_metrics[0].samplingfrequencyplane[0].value)
    ):
        return ""
    else:
        return img_node.image_metrics[0].samplingfrequencyplane[0].value


def set_img_samplingfrequencyplane(img_node, samplingfrequencyplane):
    """
    imposta il samplingfrequencyplane per l'immagine
    """
    if not img_node.image_metrics:
        img_node.image_metrics.add_instance()
    if not img_node.image_metrics[0].samplingfrequencyplane:
        img_node.image_metrics[0].samplingfrequencyplane.add_instance()
    img_node.image_metrics[0].samplingfrequencyplane[0].value = samplingfrequencyplane


def get_img_xsamplingfrequency(img_node):
    """
    ritorna il xsamplingfrequency del'immagine o dell'imggroup
    """
    if (
        (not img_node.image_metrics)
        or (not img_node.image_metrics[0].xsamplingfrequency)
        or (not img_node.image_metrics[0].xsamplingfrequency[0].value)
    ):
        return ""
    else:
        return img_node.image_metrics[0].xsamplingfrequency[0].value


def set_img_xsamplingfrequency(img_node, xsamplingfrequency):
    """
    imposta il samplingfrequencyplane per l'immagine
    """
    if not img_node.image_metrics:
        img_node.image_metrics.add_instance()
    if not img_node.image_metrics[0].xsamplingfrequency:
        img_node.image_metrics[0].xsamplingfrequency.add_instance()
    img_node.image_metrics[0].xsamplingfrequency[0].value = xsamplingfrequency


def get_img_ysamplingfrequency(img_node):
    """
    ritorna il xsamplingfrequency del'immagine o dell'imggroup
    """
    if (
        (not img_node.image_metrics)
        or (not img_node.image_metrics[0].ysamplingfrequency)
        or (not img_node.image_metrics[0].ysamplingfrequency[0].value)
    ):
        return ""
    else:
        return img_node.image_metrics[0].ysamplingfrequency[0].value


def set_img_ysamplingfrequency(img_node, ysamplingfrequency):
    """
    imposta il samplingfrequencyplane per l'immagine
    """
    if not img_node.image_metrics:
        img_node.image_metrics.add_instance()
    if not img_node.image_metrics[0].ysamplingfrequency:
        img_node.image_metrics[0].ysamplingfrequency.add_instance()
    img_node.image_metrics[0].ysamplingfrequency[0].value = ysamplingfrequency


def get_img_photometricinterpretation(img_node):
    """
    ritorna il photometricinterpretation del'immagine o dell'imggroup
    """
    if (
        (not img_node.image_metrics)
        or (not img_node.image_metrics[0].photometricinterpretation)
        or (not img_node.image_metrics[0].photometricinterpretation[0].value)
    ):
        return ""
    else:
        return img_node.image_metrics[0].photometricinterpretation[0].value


def set_img_photometricinterpretation(img_node, photometricinterpretation):
    """
    imposta il photometricinterpretation per l'immagine.
    """
    if not img_node.image_metrics:
        img_node.image_metrics.add_instance()
    if not img_node.image_metrics[0].photometricinterpretation:
        img_node.image_metrics[0].photometricinterpretation.add_instance()
    img_node.image_metrics[0].photometricinterpretation[
        0
    ].value = photometricinterpretation


def get_img_bitpersample(img_node):
    """
    ritorna i bitpersample del'immagine o dell'imggroup
    """
    if (
        (not img_node.image_metrics)
        or (not img_node.image_metrics[0].bitpersample)
        or (not img_node.image_metrics[0].bitpersample[0].value)
    ):
        return ""
    else:
        return img_node.image_metrics[0].bitpersample[0].value


def set_img_bitpersample(img_node, bitpersample):
    """
    imposta i bitpersample per l'immagine
    """
    if not img_node.image_metrics:
        img_node.image_metrics.add_instance()
    if not img_node.image_metrics[0].bitpersample:
        img_node.image_metrics[0].bitpersample.add_instance()
    img_node.image_metrics[0].bitpersample[0].value = bitpersample


def get_img_imggroup(img_node):
    """
    ritorna l'imggroup a cui si referenzia l'immagine.
    Se l'immagine non specifica un imggroup ritorna ''
    """
    if img_node.imggroupID.value:
        return img_node.imggroupID.value
    else:
        return ""


def set_img_imggroup(img_node, img_group):
    """imposta l'img_group per un'immagine"""
    img_node.imggroupID.value = img_group


## FUNZIONI SU AUDIO
## funzionano su un proxy audio


def get_audio_duration(audio_proxy):
    if (
        not audio_proxy.audio_dimensions
        or not audio_proxy.audio_proxy[0].duration
        or not audio_proxy.audio_dimensions[0].duration[0].value
    ):
        return ""
    return audio_proxy.audio_dimensions[0].audio_proxy[0].value


def set_audio_duration(audio_proxy, duration):
    if not audio_proxy.audio_dimensions:
        audio_proxy.audio_dimensions.add_instance()
    if not audio_proxy.audio_dimensions[0].duration:
        audio_proxy.audio_dimensions[0].duration.add_instance()
    audio_proxy.audio_dimensions[0].duration[0].value = duration


def get_audio_samplingfrequency(audio_proxy):
    if (
        not audio_proxy.audio_metrics
        or not audio_proxy.audio_metrics[0].samplingfrequency
        or not audio_proxy.audio_metrics[0].samplingfrequency[0].value
    ):
        return ""
    return audio_proxy.audio_metrics[0].samplingfrequency[0].value


def set_audio_samplingfrequency(audio_proxy, samplingfrequency):
    if not audio_proxy.audio_metrics:
        audio_proxy.audio_metrics.add_instance()
    if not audio_proxy.audio_metrics[0].samplingfrequency:
        audio_proxy.audio_metrics[0].samplingfrequency.add_instance()
    audio_proxy.audio_metrics[0].samplingfrequency[0].value = samplingfrequency


def get_audio_bitpersample(audio_proxy):
    if (
        not audio_proxy.audio_metrics
        or not audio_proxy.audio_metrics[0].bitpersample
        or not audio_proxy.audio_metrics[0].bitpersample[0].value
    ):
        return ""
    return audio_proxy.audio_metrics[0].bitpersample[0].value


def set_audio_bitpersample(audio_proxy, bitpersample):
    if not audio_proxy.audio_metrics:
        audio_proxy.audio_metrics.add_instance()
    if not audio_proxy.audio_metrics[0].bitpersample:
        audio_proxy.audio_metrics[0].bitpersample.add_instance()
    audio_proxy.audio_metrics[0].bitpersample[0].value = bitpersample


def get_audio_bitrate(audio_proxy):
    if (
        not audio_proxy.audio_metrics
        or not audio_proxy.audio_metrics[0].bitrate
        or not audio_proxy.audio_metrics[0].bitrate[0].value
    ):
        return ""
    return audio_proxy.audio_metrics[0].bitrate[0].value


def set_audio_bitrate(audio_proxy, bitrate):
    if not audio_proxy.audio_metrics:
        audio_proxy.audio_metrics.add_instance()
    if not audio_proxy.audio_metrics[0].bitrate:
        audio_proxy.audio_metrics[0].bitrate.add_instance()
    audio_proxy.audio_metrics[0].bitrate[0].value = bitrate


def set_audio_compression(audio_proxy, compression):
    if not audio_proxy.format:
        audio_proxy.format.add_instance()
    if not audio_proxy.format[0].compression:
        audio_proxy.format[0].compression.add_instance()
    audio_proxy.format[0].compression[0].value = compression


def get_audio_compression(audio_proxy):
    if (
        not audio_proxy.format
        or not audio_proxy.format[0].compression
        or not audio_proxy.format[0].compression[0].value
    ):
        return ""
    return audio_proxy.format[0].compression[0].value


def get_audio_channel_configuration(audio_proxy):
    if (
        not audio_proxy.format
        or not audio_proxy.format[0].channel_configuration
        or not audio_proxy.format[0].channel_configuration[0].value
    ):
        return ""
    return audio_proxy.format[0].channel_configuration[0].value


def set_audio_channel_configuration(audio_proxy, channel_configuration):
    if not audio_proxy.format:
        audio_proxy.format.add_instance()
    if not audio_proxy.format[0].channel_configuration:
        audio_proxy.format[0].channel_configuration.add_instance()
    audio_proxy.format[0].channel_configuration[0].value = channel_configuration


## FUNZIONI SU VIDEO
## funzionano su un proxy video


def get_video_duration(video_proxy):
    if not video_proxy.video_dimensions:
        return ""
    return video_proxy.video_dimensions[0].duration.get_value() or ""


def set_video_duration(video_proxy, duration):
    if not video_proxy.video_dimensions:
        video_proxy.video_dimensions.add_instance()
    video_proxy.video_dimensions[0].duration.set_value(duration)


def get_video_videoformat(video_proxy):
    if not video_proxy.format:
        return ""
    return video_proxy.format[0].videoformat.get_value() or ""


def set_video_videoformat(video_proxy, videoformat):
    if not video_proxy.format:
        video_proxy.format.add_instance()
    video_proxy.format[0].videoformat.set_value(videoformat)


def set_video_streamtype(video_proxy, streamtype):
    if not video_proxy.format:
        video_proxy.format.add()
    video_proxy.format[0].streamtype.set_value(streamtype)


def set_video_codec(video_proxy, codec):
    if not video_proxy.format:
        video_proxy.format.add()
    video_proxy.format[0].codec.set_value(codec)


def set_video_videosize(video_proxy, videosize):
    if not video_proxy.video_metrics:
        video_proxy.video_metrics.add()
    video_proxy.video_metrics[0].videosize.set_value(videosize)


def set_video_aspectratio(video_proxy, aspectratio):
    if not video_proxy.video_metrics:
        video_proxy.video_metrics.add()
    video_proxy.video_metrics[0].aspectratio.set_value(aspectratio)


def set_video_framerate(video_proxy, framerate):
    if not video_proxy.video_metrics:
        video_proxy.video_metrics.add()
    video_proxy.video_metrics[0].framerate.set_value(framerate)


##


def resource_node_sort_key(rsrc_node):
    """Return a key suitable to be used to sort resource nodes

    The key will be the int value of the resource sequence number.
    Resources without sequence number will always have a lower key.

    """
    try:
        return int(get_resource_sequence_number(rsrc_node))
    except ValueError:
        return -1


# FUNZIONI SUI GRUPPI DI RISORSE


def get_imggroup(imggroup_node, id):
    """ritorna l'imggroup con id img_group_id fra quelli
    dell'elenco imggroup_node"""
    for imggroup in imggroup_node:
        imggroup_id = get_imggroup_id(imggroup)
        if imggroup_id == id:
            return imggroup
    return None


def get_imggroup_id(imggroup):
    """ritorna l'id di un imggroup"""
    if imggroup.ID.value:
        return imggroup.ID.value
    else:
        return ""


# FUNZIONI SUI CONTLET


def get_contlet_identifier(contlet):
    """
    ritorna il valore dell'identifier Dublin Core di un contlet. Se il contlet non ha
    identifier, viene ritornata la stringa vuota
    """
    if (not contlet.identifier) and (not contlet.identifier[0].value):
        return ""
    else:
        return contlet.identifier[0].value


def get_contlet_resource_document(resource):
    """
    ritorna il documento a cui si riferisce la risorsa del contlet. Se la risorsa non specifica
    un documento di riferimento, e quindi si assume si riferisca al documento stesso, ritorna la
    stringa vuota
    """
    if (not resource.location) or (not resource.location[0].value):
        return ""
    else:
        return resource.location[0].value


def set_contlet_resource_document(resource, resource_document):
    """
    imposta un nuovo documento di riferimento per la risorsa.
    se viene passato un resource_document vuoto, il campo che contiene il documento
    di riferimento viene rimosso dalla risorsa
    """
    if (not resource_document) and (resource.location):
        resource.location.DelInstance()
    else:
        if not resource.location:
            resource.location.add_instance()
        resource.location[0].value = resource_document


def get_contlet_resource_type(resource):
    """
    ritorna il tipo fisico della risorsa (img, doc, video....)
    la risorsa può avere un solo elemento fisico img_element, video_element, doc_element .....
    viene ritorna il nome di questo elemento, senza suffisso _element
    """
    for element in (
        "img_element",
        "video_element",
        "doc_element",
        "ocr_element",
        "audio_element",
        "semantic_element",
    ):
        if getattr(resource, element):
            return element[:-8]
    return None


def set_contlet_resource_type(resource, new_type):
    """
    imposta un nuovo tipo fisico per la risorsa del contlet.
    il tipo fisico vecchio viene rimosso, insieme a tutte le sue specifiche (seq_ns, sezioni media)
    se si passa un new_type nullo, la risorsa rimarrà senza sezione fisica
    """
    if (new_type) and (
        new_type not in ("img", "video", "doc", "ocr", "audio", "semantic")
    ):
        raise valueError('Valore scorretto per il tipo di risorsa: "%s"' % new_type)

    #   if getattr(resource, new_type+'_element'):
    #       return # il tipo c'è già
    # rimuovo i tipi presenti
    for element in (
        resource.img_element,
        resource.video_element,
        resource.doc_element,
        resource.ocr_element,
        resource.audio_element,
        resource.semantic_element,
    ):
        if element:
            element.DelInstance()
    if new_type:
        getattr(resource, new_type + "_element").add_instance()


def get_contlet_resource_seq_ns(resource):
    """
    ritorna un'elenco di intervalli di sequence_number a cui si riferisce la risorsa
    nella forma ( (inizio, fine), (inizio, fine) ... )
    """
    results = []
    # la risorsa ha uno ed uno solo dei possibili elementi fisici, prendo il primo che trovo
    for element in (
        resource.img_element,
        resource.video_element,
        resource.doc_element,
        resource.ocr_element,
        resource.audio_element,
        resource.semantic_element,
    ):
        if element:
            phy_element = element[0]
            break
    else:  # se non ha elementi fisici ritorno la lista vuota
        # raise Exception('La risorsa del contlet non ha un elemento fisico, impossibile recuperare i sequence number')
        return results

    # i seq_n sono tenuti nel sottoelemento sequence_numbers, se non c'è esco
    if phy_element.sequence_numbers:
        seq_ns_element = phy_element.sequence_numbers[0]
    else:
        return results

    # l'element ha i sequence number specificati come singoli nel sottoelement sequence_number,
    # e come intervalli in sequence_interval. Anche se specifica i seq_n come singoli, essi vengono
    # ritornati come intervallo (singolo, singolo)
    for seq_n in [
        single_seq_n.value
        for single_seq_n in seq_ns_element.sequence_number
        if single_seq_n.value
    ]:
        results.append((int(seq_n), int(seq_n)))

    for seq_interval in seq_ns_element.sequence_interval:
        if (
            (not seq_interval.start_sequence_number)
            or (not seq_interval.start_sequence_number[0].value)
            or (not seq_interval.stop_sequence_number)
            or (not seq_interval.stop_sequence_number[0].value)
        ):
            # il sequence_interval non è completo, non lo aggiungo
            pass
        else:
            results.append(
                (
                    int(seq_interval.start_sequence_number[0].value),
                    int(seq_interval.stop_sequence_number[0].value),
                )
            )
    return results


def set_contlet_resource_seq_n(resource, seq_n):
    """
    aggiunge un sequence_number per la risorsa del contlet, a prescindere dal tipo fisico della risorsa
    """
    for element in (
        resource.img_element,
        resource.video_element,
        resource.doc_element,
        resource.ocr_element,
        resource.audio_element,
        resource.semantic_element,
    ):
        if element:  # trovo l'elemento fisico della risorsa
            phy_element = element[0]
            break

    if not phy_element.sequence_numbers:
        # se l'elemento fisico non ha l'elemento per i seq_n, lo aggiungo
        phy_element.sequence_numbers.add_instance()

    seq_numbers_element = phy_element.sequence_numbers[0]

    seq_numbers_element.sequence_number.add_instance()  # aggiungo un element per un singolo seq_n
    # imposto il valore dell'ultimo elemento aggiunti
    seq_numbers_element.sequence_number[-1].value = str(seq_n)


def set_contlet_resource_seq_interval(resource, start_seq_n, stop_seq_n):
    """
    aggiunge un intervallo di seq_n per la risorsa del contlet,
    a prescindere dal tipo fisico della risorsa
    """
    for element in (
        resource.img_element,
        resource.video_element,
        resource.doc_element,
        resource.ocr_element,
        resource.audio_element,
        resource.semantic_element,
    ):
        if element:  # trovo l'elemento fisico della risorsa
            phy_element = element[0]
            break

    if not phy_element.sequence_numbers:
        # se l'elemento fisico non ha l'elemento per i seq_n, lo aggiungo
        phy_element.sequence_numbers.add_instance()

    seq_numbers_element = phy_element.sequence_numbers[0]

    seq_numbers_element.sequence_interval.add_instance()

    seq_interval_element = seq_numbers_element.sequence_interval[-1]

    seq_interval_element.start_sequence_number.add_instance(str(start_seq_n))
    seq_interval_element.stop_sequence_number.add_instance(str(stop_seq_n))


def clear_contlet_resource(resource):
    """
    svuota la risorsa del contlet
    """
    set_contlet_resource_type(resource, "")
    if resource.location:
        resource.location.DelInstance()


def get_ontologic_link_ontology(ontologic_link):
    """
    ritorna l'ontologia a cui si riferisce un link ontologico,
    o la stringa vuota se esso non la esprime
    """
    if (not ontologic_link.ontology) or (not ontologic_link.ontology[0].value):
        return ""
    else:
        return ontologic_link.ontology[0].value


def get_ontologic_link_instance(ontologic_link):
    """
    ritorna l'istanza base del link ontologico
    """
    if (
        (not ontologic_link.instance)
        or (not ontologic_link.instance[0].base_instance)
        or (not ontologic_link.instance[0].base_instance[0].value)
    ):
        return ""
    else:
        return ontologic_link.instance[0].base_instance[0].value


def get_ontologic_link_property_predicate(ontology_property):
    """
    ritorna il predicato di una proprietà di un link ontologico
    """
    if (not ontology_property.predicate) or (not ontology_property.predicate[0].value):
        return ""
    else:
        return ontology_property.predicate[0].value


def get_ontologic_link_property_object(ontology_property):
    """
    ritorna l'oggetto di una proprietà di un link ontologico
    """
    if (not ontology_property.object) or (not ontology_property.object[0].value):
        return ""
    else:
        return ontology_property.object[0].value


def get_ontologic_link_matching(ontologic_link):
    """
    ritorna il matching del link ontologico, o '' se questo non è espresso
    """
    if (not ontologic_link.matching) or (not ontologic_link.matching[0].value):
        return ""
    else:
        return ontologic_link.matching[0].value


def get_geolink_relation(geolink):
    """
    ritorna la lista di relazioni espresse da un link geografico
    """
    results = []
    valid_relations = ("was_created_in", "represents", "describes", "is_in")
    for relation in geolink.relation:
        if relation.value:
            if relation.value in valid_relations:
                results.append(relation.value)
            else:
                raise ValueError(
                    'Tipo di relazione per un geolink non permesso: "%s"'
                    % relation.value
                )
    return results


def get_geolink_position_latitude(geolink):
    """
    ritorna la latitudine di un link geografico
    """
    if (
        (not geolink.position)
        or (not geolink.position[0].point)
        or (not geolink.position[0].point[0].latitude)
        or (not geolink.position[0].point[0].latitude[0].value)
    ):
        return ""
    else:
        return geolink.position[0].point[0].latitude[0].value


def get_geolink_position_longitude(geolink):
    """ritorna la latitudine di un link geografico"""
    if (
        (not geolink.position)
        or (not geolink.position[0].point)
        or (not geolink.position[0].point[0].longitude)
        or (not geolink.position[0].point[0].longitude[0].value)
    ):
        return ""
    else:
        return geolink.position[0].point[0].longitude[0].value


def get_geolink_position_radius(geolink):
    """ritorna il raggio e la sua unità di misura di una link geografico"""
    if (not geolink.position) or (not geolink.position[0].radius):
        return ("", "")
    if not geolink.position[0].radius[0].value:
        radius = ""
    else:
        radius = geolink.position[0].radius[0].value
    if not (geolink.position[0].radius[0].unit.value):
        unit = ""
    else:
        unit = geolink.position[0].radius[0].unit.value
    return radius, unit
