import hashlib
import logging
import mimetypes
import os
import re
import stat
import subprocess
import time
import wave

import PIL.Image

from maglib.utils import mag_wrapper, misc

logger = logging.getLogger(__name__)


# eyed3 opzionale per metadati mp3
try:
    import eyed3

    EYED3 = True
except ImportError:
    EYED3 = False

if not EYED3:
    logger.warning("Modulo eyed3 non trovato metadati mp3 disabilitati")


class Resource_info_importer(object):
    """questa classe importa le informazioni file all'interno del nodo media
    ( img, video, doc ... ) del MAG prendendole dal file a cui
    si riferisce il nodo"""

    def __init__(
        self,
        resource_node,
        resource_basepath,
        calc_md5=False,
        md5_progress=None,
        md5_stop=None,
    ):
        """resource_node è il singolo nodo del mag
        resource_basepath è il path da cui inizia il path scritto
           nel nodo della risorsa"""
        self.resource_node = resource_node

        resource_partial_path = mag_wrapper.get_resource_filepath(self.resource_node)

        if not resource_partial_path:
            logger.warning("resource has not path, ignoring it")
            return

        self.resource_path = os.path.join(resource_basepath, resource_partial_path)
        self._calc_md5 = calc_md5
        self._md5_progress = md5_progress if md5_progress else [0]
        self._md5_stop = md5_stop if md5_stop else [False]
        self._import()

    def _build_resource_info(self):
        return File_info_extractor(
            self.resource_path, self._calc_md5, self._md5_progress, self._md5_stop
        )

    def _get_info_maps(self):
        """questo metodo deve ritornare una lista di coppie di stringhe.
        Il primo elemento verrà usato per estrarre (con un interfaccia
        tipo-dizionario) il valore dell'info dall'oggetto che legge le info
        (derivante da Abstract_file_info_extractor).
        Il secondo elemento viene usato per scegliere il metodo impostatore
        dal modulo mag_wrapper; il metodo ha questa segnatura:
        setter_method(resource_node, value)"""
        info_maps = (
            ("mimetype", "set_resource_format_mimetype"),
            ("formatname", "set_resource_format_name"),
            ("datetimecreated", "set_resource_datetimecreated"),
            ("filesize", "set_resource_filesize"),
            ("md5", "set_resource_md5"),
        )

        return info_maps

    def _import(self):
        self._resource_info = self._build_resource_info()

        for info_key, method_name in self._get_info_maps():
            if info_key in self._resource_info:
                info_value = self._resource_info[info_key]
                setter_method = getattr(mag_wrapper, method_name)
                setter_method(self.resource_node, info_value)


class Img_info_importer(Resource_info_importer):
    """questa classe importa le informazioni su un'immagine all'interno
    di un nodo MAG img"""

    def __init__(self, img_group, *args, **kwargs):
        """img_group è l'imggroup a cui si riferisce l'immagine, serve per
        controllare di non inserire valori ripetuti rispetto ad esso"""
        self.img_group = img_group
        super().__init__(*args, **kwargs)

    def _build_resource_info(self):
        return Img_info_extractor(
            "2",
            "2",
            self.resource_path,
            self._calc_md5,
            self._md5_progress,
            self._md5_stop,
        )

    def _get_info_maps(self):
        info_maps = (
            ("xsamplingfrequency", "set_img_xsamplingfrequency"),
            ("ysamplingfrequency", "set_img_ysamplingfrequency"),
            ("samplingfrequencyplane", "set_img_samplingfrequencyplane"),
            ("samplingfrequencyunit", "set_img_samplingfrequencyunit"),
            ("photometricinterpretation", "set_img_photometricinterpretation"),
            ("bitpersample", "set_img_bitpersample"),
            ("imagelength", "set_img_length"),
            ("imagewidth", "set_img_width"),
            ("compression", "set_resource_format_compression"),
        )
        return super()._get_info_maps() + info_maps

    def _import(self):
        super()._import()
        self._img_lint()

    def _img_lint(self):
        # rimuove dal nodo immagine alcuni nodi, o se non sono validi o
        # se includono informazioni ripetuti con quelle dell'img_group
        for (val_method, cmp_method, node_name) in (
            (self._validate_img_metrics, self._cmp_img_metrics, "image_metrics"),
            (self._validate_img_format, self._cmp_img_format, "format"),
        ):
            if not getattr(self.resource_node, node_name):
                continue

            if not val_method():
                logger.warning(
                    "Nodo % s dell'immagine %s rimosso in quanto non valido",
                    node_name,
                    self.resource_path,
                )
                getattr(self.resource_node, node_name).clear()
            # il confronto col gruppo si fa solo se il gruppo non è None
            elif self.img_group and cmp_method():
                logger.debug(
                    "Nodo %s dell'immagine %s rimosso "
                    % (node_name, self.resource_path)
                    + "in quanto duplicato di quello dell'img_group"
                )
                getattr(self.resource_node, node_name).clear()

    def _validate_img_metrics(self):
        for method in (
            mag_wrapper.get_img_samplingfrequencyunit,
            mag_wrapper.get_img_samplingfrequencyplane,
            mag_wrapper.get_img_photometricinterpretation,
            mag_wrapper.get_img_bitpersample,
        ):
            if not method(self.resource_node):
                return False
        return True

    def _cmp_img_metrics(self):
        # dice se image_metrics dell'immagine è uguale a quello del gruppo
        for method in (
            mag_wrapper.get_img_samplingfrequencyunit,
            mag_wrapper.get_img_samplingfrequencyplane,
            mag_wrapper.get_img_photometricinterpretation,
            mag_wrapper.get_img_bitpersample,
            mag_wrapper.get_img_xsamplingfrequency,
            mag_wrapper.get_img_ysamplingfrequency,
        ):
            if method(self.img_group) != method(self.resource_node):
                return False
        return True

    def _validate_img_format(self):
        for method in (
            mag_wrapper.get_resource_format_name,
            mag_wrapper.get_resource_format_mimetype,
            mag_wrapper.get_resource_format_compression,
        ):
            if not method(self.resource_node):
                return False
        return True

    def _cmp_img_format(self):
        for method in (
            mag_wrapper.get_resource_format_name,
            mag_wrapper.get_resource_format_mimetype,
            mag_wrapper.get_resource_format_compression,
        ):
            if method(self.resource_node) != method(self.img_group):
                return False
        return True


class Doc_info_importer(Resource_info_importer):
    """questa classe importa le informazioni su un documento di testo
    all'interno di un nodo MAG doc o ocr"""

    def _build_resource_info(self):
        return Doc_info_extractor(
            self.resource_path, self._calc_md5, self._md5_progress, self._md5_stop
        )

    def _get_info_maps(self):
        info_maps = (("compression", "set_resource_format_compression"),)
        return super()._get_info_maps() + info_maps


class Audio_info_importer(Resource_info_importer):
    """questa classe importa le informazioni su un file audio all'interno
    di un nodo MAG audio proxy. Non considera gli audio_group eventuali
    del mag. Lavora su un audio proxy"""

    def _build_resource_info(self):
        return Audio_info_extractor(
            self.resource_path, self._calc_md5, self._md5_progress, self._md5_stop
        )

    def _get_info_maps(self):
        return (
            ("duration", "set_audio_duration"),
            ("samplingfrequency", "set_audio_samplingfrequency"),
            ("bitpersample", "set_audio_bitpersample"),
            ("bitrate", "set_audio_bitrate"),
            ("compression", "set_audio_compression"),
            ("channel_configuration", "set_audio_channel_configuration"),
        ) + super()._get_info_maps()


class Video_info_importer(Resource_info_importer):
    """questa classe importa le informazioni di un file video all'interno di
    un nodo MAG video proxy. Non considera i video_group eventuali del mag."""

    def _build_resource_info(self):
        return Video_info_extractor(
            self.resource_path, self._calc_md5, self._md5_progress, self._md5_stop
        )

    def _import(self):
        super()._import()

        # se ho gli elementi minimi sufficienti per video_metrics,
        # provo ad aggiungere i suoi tre figli
        # comunque elimino prima spatialmetrics se presente,
        # in quanto potrebbe essere non valido
        self.resource_node.video_metrics.clear()
        if self._resource_info.get("videosize") and self._resource_info.get(
            "framerate"
        ):

            mag_wrapper.set_video_videosize(
                self.resource_node, self._resource_info["videosize"]
            )
            mag_wrapper.set_video_framerate(
                self.resource_node, self._resource_info["framerate"]
            )
            if self._resource_info["aspectratio"]:
                mag_wrapper.set_video_aspectratio(
                    self.resource_node, self._resource_info["aspectratio"]
                )

    def _get_info_maps(self):
        return (
            ("duration", "set_video_duration"),
            ("videoformat", "set_video_videoformat"),
            ("streamtype", "set_video_streamtype"),
            ("codec", "set_video_codec"),
        ) + super()._get_info_maps()


class Abstract_file_info_extractor(dict):
    """questa classe rappresenta un astratto estrattore di informazioni da un file
    le informazioni raccolte vengono recuperate attraverso un'interfaccia da
    dizionario"""

    # definire questo dizionario per mappare mimetype su nomi
    # formati (vedi _get_format_name)
    formats_mapping = {}
    # definire questo dizionario per tradurre mimetype (ved _get_mimetype)
    mimetype_transform = {}

    def __init__(self, filepath):
        """filepath è il path del file da analizzare."""

        self.filepath = filepath

        try:
            fp = open(filepath, "rb")
        except (IOError, OSError):
            logger.warning("cannot open file %s, ignoring it", filepath)
            return
        with fp:
            self._build_dict(fp)

    def _get_format_name(self, mimetype):
        """oltre al mimetype, nel MAG c'è il nome del formato come
        stringa di tre lettere. quì converto da mimetype e nome del formato"""
        try:
            return self.formats_mapping[mimetype]
        except KeyError:
            return None

    def _get_mimetype(self):
        mimetype = mimetypes.guess_type(self.filepath)[0]
        if mimetype:
            try:
                return self.mimetype_transform[mimetype]
            except KeyError:
                return mimetype
        return None

    def _build_dict(self, file_handler):
        pass  # riempire il dizionario quì


class File_info_extractor(Abstract_file_info_extractor):
    """definisce le seguenti informazioni:
    - mimetype (opzionale)
    - formatname (opzionale)
    - datetimecreated
    - filesize
    - md5 (opzionale)"""

    def __init__(self, filepath, calc_md5, md5_progress, md5_stop, md5_bufsize=8192):
        """calc_md5 indica se calcolare l'md5
        md5_calc_progress è una lista nel cui primo elemento viene scritto
           l'avanzamento del calcolo dell'md5
        md5_bufsize è il buffer in byte per il calcolo dell'md5"""
        self._calc_md5 = calc_md5
        self._md5_bufsize = md5_bufsize
        self._md5_progress = md5_progress
        self._md5_stop = md5_stop
        super().__init__(filepath)

    def _build_dict(self, file_handler):
        mimetype = self._get_mimetype()
        if mimetype:
            self["mimetype"] = mimetype
            formatname = self._get_format_name(mimetype)
            if formatname:
                self["formatname"] = formatname

        self.file_stat = os.fstat(file_handler.fileno())
        # la data viene inserita subito in formato iso
        self["datetimecreated"] = misc.iso8601_time(self.file_stat[stat.ST_CTIME])
        self["filesize"] = str(self.file_stat[stat.ST_SIZE])

        if self._calc_md5:
            self["md5"] = self._build_md5(file_handler)

    def _build_md5(self, file_handler):
        hasher = hashlib.md5()
        self._md5_progress[0] = 0
        buf = file_handler.read(self._md5_bufsize)
        while buf:
            if self._md5_stop[0]:
                self._md5_progress[0] = -1
                return
            hasher.update(buf)
            self._md5_progress[0] += self._md5_bufsize
            buf = file_handler.read(self._md5_bufsize)
        self._md5_progress[0] = -1
        return hasher.hexdigest()


class Img_info_extractor(File_info_extractor):
    """raccoglie le informazioni specifiche dei file immagine
    usando la libreria PIL.
    Informazioni definite:
    - xsamplingfrequency ( opzionale )
    - ysamplingfrequency ( opzionale )
    - samplingfrequencyplane ( opzionale se non si indica un valore di
      default nel costruttore)
    - samplingfrequencyunit ( messo fisso a 2 )
    - photometricinterpretation
    - bitpersample ( opzionale )
    - imagelength
    - imagewidth
    - compression ( opzionale )"""

    formats_mapping = {
        "image/tiff": "TIF",
        "image/jpeg": "JPG",
        "image/png": "PNG",
        "image/gif": "GIF",
    }
    mimetype_transform = File_info_extractor.mimetype_transform.copy()
    mimetype_transform.update({"image/pjpeg": "image/jpeg"})

    DEF_SAMPLINGFREQUENCYPLANE = "1"

    def __init__(self, sampling_plane=False, sampling_unit="2", *args, **kwargs):
        """
        :sampling_plane: samplingfrequencyplane da inserire fra le informazioni
        se False, si prova a ricavare automaticamente. se si fallisce varrà
        DEF_SAMPLINGFREQUENCYPLANE
        :sampling_unit: samplingfrequencyunit da inserire fra le informazioni,
        non può essere False visto che non si può ricavare automaticamente"""
        self._sampling_plane = sampling_plane
        self._sampling_unit = sampling_unit
        super().__init__(*args, **kwargs)

    def _build_dict(self, file_handler):
        super()._build_dict(file_handler)
        self.img = PIL.Image.open(self.filepath)

        self._get_dpi()
        self._get_colorspace()
        self._get_sampling_plane()
        self._get_dimensions()
        self._get_compression()

    def _get_dpi(self):
        """ottiene la coppia frequenza di campionamento orizzontale/verticale"""

        try:  # provo nel dizionario info dell'immagine
            self["xsamplingfrequency"], self["ysamplingfrequency"] = [
                str(int(x)) for x in self.img.info["dpi"]
            ]
            return
        except KeyError:
            pass

        # le immagini tiff possono avere i dpi scritti nei tag 282 e 283
        if self.img.format == "TIFF":
            tag_282 = self.img.tag.get(282)
            if tag_282:
                self["xsamplingfrequency"] = str(tag_282[0][0] // tag_282[0][1])
            tag_283 = self.img.tag.get(283)
            if tag_283:
                self["ysamplingfrequency"] = str(tag_283[0][0] // tag_283[0][1])

    def _get_sampling_plane(self):
        if not self._sampling_plane:
            if hasattr(self.img, "_planar_configuration"):
                self["samplingfrequencyplane"] = str(self.img._planar_configuration)
            else:
                self["samplingfrequencyplane"] = self.DEF_SAMPLINGFREQUENCYPLANE
        else:
            self["samplingfrequencyplane"] = self._sampling_plane

        self["samplingfrequencyunit"] = self._sampling_unit

    def _get_colorspace(self):
        """ottiene lo schema del colore di un'immagine"""
        if self.img.mode == "RGBA":
            self["photometricinterpretation"] = "RGB"
        elif self.img.mode == "L" and self.img.format == "TIFF":
            # colore scala di grigi, devo vedere il tag tiff
            # photometricinterpretation
            #  (0 nero o bianco )per esprimere il campo come lo vuole ilmag
            if self.img.tag.get(262)[0] == 0:
                self["photometricinterpretation"] = "WhiteIsZero"
            elif self.img.tag.get(262)[0] == 1:
                self["photometricinterpretation"] = "BlackIsZero"
        elif self.img.mode == "L" and self.img.format == "JPEG":
            self["photometricinterpretation"] = "BlackIsZero"  # ??
        else:  # negli altri casi non trasformo il campo
            self["photometricinterpretation"] = self.img.mode

        if self.img.mode in ("RGBA", "RGB"):
            self["bitpersample"] = "8,8,8"
        elif self.img.mode == "L":
            self["bitpersample"] = "8"

    def _get_dimensions(self):
        self["imagewidth"] = str(self.img.size[0])
        self["imagelength"] = str(self.img.size[1])

    def _get_compression(self):
        if self.img.format == "JPEG":  # una JPEG è sempre compressa in JPEG
            self["compression"] = "JPG"
            return

        if self.img.format == "PNG":
            self["compression"] = "PNG"
            return

        if self.img.format == "TIFF":  # per le tiff guardo nel tag 259
            compression = self.img.tag.get(259)[0]
            compression_mapping = {
                1: "Uncompressed",
                2: "CCITT ID",
                3: "Group 3 Fax",
                4: "CCITT Group 4",
                5: "LZW",
                6: "JPEG",
            }
            try:
                self["compression"] = compression_mapping[compression]
                return
            except KeyError:
                pass

        if "compression" in self.img.info:
            # come ultima risorsa guardo se PIL ha capito qualcosa
            compression = self.img.info["compression"]
            compression_mapping = {"tiff_lzw": "LZW", "raw": "Uncompressed"}
            if compression in compression_mapping:
                self["compression"] = compression


class Audio_info_extractor(File_info_extractor):
    """raccoglie informazioni su un file audio. Definisce le seguenti informazioni:
    -duration
    -samplingfrequency (opzionale)
    -bitpersample (opzionale)
    -bitrate (opzionale)
    -compression (opzionale)
    -channel_configuration (opzionale)"""

    formats_mapping = {"audio/wav": "WAV", "audio/x-wav": "WAV", "audio/mpeg": "MP3"}
    mimetype_transform = {"audio/x-wav": "audio/wav", "audio/x-mpg": "audio/mpeg"}

    def _build_dict(self, file_handler):
        super()._build_dict(file_handler)
        if self["mimetype"] == "audio/x-mpg":
            self["mimetype"] = "audio/x-mpeg"

        if self["mimetype"] in ("audio/x-wav", "audio/wav"):
            self._build_dict_wav()
        elif self["mimetype"] in ("audio/mpeg", "audio/x-mpeg"):
            self._build_dict_mp3()

    def _build_dict_mp3(self):
        if not EYED3:
            # per avere comunque il mag validato
            self["duration"] = "00:00:00"
            logger.warning(
                "modulo eyed3 assente, durata fittizia per %s", self.filepath
            )
            return

        mp3_info = Eyed3Mp3Info(self.filepath)

        # TODO: calcolare in millisecondi
        # duration = mp3.getPlayTime()
        self["duration"] = self._convert_duration(mp3_info.duration)

        self._read_mp3_frequency(mp3_info)
        self._read_mp3_bitrate(mp3_info)

        layer = self._map_mp3_layer(mp3_info.layer)
        if layer:
            self["compression"] = layer

        mode = mp3_info.mode
        if mode:
            self["channel_configuration"] = mode

    def _build_dict_wav(self):
        try:
            wave_read = wave.open(self.filepath)
        except wave.Error:
            # per avere comunque il mag validato
            self["duration"] = "00:00:00"
            logger.warning(
                "impossibile comprendere %s, inserita durata fittizia", self.filepath
            )
            return

        frequency = wave_read.getframerate()
        n_frames = wave_read.getnframes()
        duration = float(n_frames) / frequency
        self["duration"] = self._convert_duration(duration)
        frequency = self._convert_frequency(frequency)
        if frequency:
            self["samplingfrequency"] = frequency
        bitpersample = wave_read.getsampwidth() * 8  # mi serve il valore in bit
        if bitpersample in (8, 16, 24):
            self["bitpersample"] = str(bitpersample)
        if wave_read.getcomptype() == "NONE":
            self["compression"] = "Uncompressed"

        channels = wave_read.getnchannels()
        if channels == 1:
            self["channel_configuration"] = "Mono"
        elif channels == 2:
            self["channel_configuration"] = "Stereo"

    def _convert_frequency(self, frequency):
        # converte la frequenza da intero a stringa
        frequency = "%f" % (frequency / 1000.0)
        # elimino 0 e punto finale, se inutili
        frequency = re.sub(r"\.?0*$", "", frequency)
        # TODO: controllare che la frequenza sia fra quelle consentite
        return frequency

    def _read_mp3_frequency(self, mp3_info):
        if not mp3_info.sample_freq:
            return
        self["samplingfrequency"] = self._convert_frequency(mp3_info.sample_freq)

    def _read_mp3_bitrate(self, mp3_info):
        if mp3_info.vbr:
            logger.warning("mp3 VBR, inserimento bitpersample fittizio")
            self["bitpersample"] = "16"
        else:
            self["bitrate"] = str(mp3_info.bit_rate)

    def _map_mp3_layer(self, layer):
        # mappa il layer mp3 sul tipo di compressione che vuole il mag
        layer_map = {3: "MPEG-1 layer 3"}
        return layer_map.get(layer, None)

    def _convert_duration(self, seconds):
        # converte la durata in secondi in durata in formato xsd:time
        hours = minutes = 0
        while seconds >= 3600:
            hours += 1
            seconds -= 3600
        while seconds >= 60:
            minutes += 1
            seconds -= 60
        decimal = seconds - int(seconds)
        decimal_string = ("%f" % decimal).split(".")[1]
        seconds = int(seconds)
        return "%02d:%02d:%02d.%s" % (hours, minutes, seconds, decimal_string)


class Video_info_extractor(File_info_extractor):
    """raccoglie le informazioni su un file video.
    Definisce le seguenti informazioni:
    -duration
    -videoformat
    -streamtype (opzionale)
    -videosize (opzionale)
    -aspectratio (opzionale)
    -framerate (opzionale)
    -codec
    """

    formats_mapping = {
        "video/avi": "AVI",
        "video/mpeg": "MPEG",
        "video/wmv": "WMV",
        "video/quicktime": "MOV",
    }
    mimetype_transform = {
        "video/mp4": "video/mpeg",
        "video/x-ms-wmv": "video/wmv",
        "video/x-msvideo": "video/avi",
    }

    # videosize permessi dallo standard
    _allowed_video_size = {
        "160x120",
        "176x144",
        "192x144",
        "280x180",
        "320x240",
        "352x288",
        "360x288",
        "384x288",
        "480x576",
        "720x576",
    }

    # aspectratio permessi
    _allowed_aspectratio = {"1:1", "4:3", "16:9", "2.11:1"}

    # framerate permessi
    _allowed_framerate = {"23.976", "24", "25", "29.97", "30", "50", "59.94", "60"}

    def _build_dict(self, file_handler):
        super()._build_dict(file_handler)

        if os.path.splitext(self.filepath)[1].lower() == ".vob":
            self["mimetype"] = "video/mpeg"
            self["formatname"] = "VOB"

        self["videoformat"] = "Unspecified"

        ffprobe_info = FFProbeInfo(self.filepath)

        if ffprobe_info.duration:
            self["duration"] = self._convert_ffprobe_duration(ffprobe_info.duration)
        else:
            logger.warning("inserting fake duration")
            self["duration"] = "00:00:00"

        self["codec"] = ffprobe_info.codec

        if ffprobe_info.codec == "mpeg2video":
            self["streamtype"] = "MPEG-2"
        elif ffprobe_info.codec == "h264":
            self["streamtype"] = "MPEG-4"

        if ffprobe_info.size:
            if ffprobe_info.size not in self._allowed_video_size:
                logger.warning(
                    'inserting unsupported video size "%s"', ffprobe_info.size
                )
            self["videosize"] = ffprobe_info.size

        if ffprobe_info.aspect_ratio:
            if ffprobe_info.aspect_ratio not in self._allowed_aspectratio:
                logger.info(
                    'inserting unsupported aspect_ratio "%s"', ffprobe_info.aspect_ratio
                )
            self["aspectratio"] = ffprobe_info.aspect_ratio

        if ffprobe_info.framerate:
            if ffprobe_info.framerate not in self._allowed_framerate:
                logger.warning(
                    'inserting unsupported video framerate "%s"',
                    self._allowed_framerate,
                )
            self["framerate"] = ffprobe_info.framerate

    @classmethod
    def _convert_ffprobe_duration(self, s):
        # 321323.0142
        seconds, rest = s.split(".")
        t = time.gmtime(int(seconds))
        assert t.tm_hour < 24
        duration = "%02d:%02d:%02d" % (t.tm_hour, t.tm_min, t.tm_sec)
        if rest.rstrip("0"):
            duration += ".%s" % rest.rstrip("0")
        return duration


class Doc_info_extractor(File_info_extractor):
    """raccoglie alcune informazioni specifiche ai documenti di testo
    (testo semplice, word processor, pdf). Definisce le seguenti informazioni:
    - compression ( opzionale )"""

    formats_mapping = {
        "text/plain": "TXT",
        "application/pdf": "PDF",
        "text/html": "HTM",
        "text/xml": "XML",
        "application/msword": "DOC",
        "text/rtf": "DOC",
    }
    mimetype_transform = {
        # MAG accetta solo text/xml e text/rtf
        "application/xml": "text/xml",
        "application/rtf": "text/rtf",
    }

    def _build_dict(self, file_handler):
        super()._build_dict(file_handler)
        if self.get("mimetype") in (
            "text/plain",
            "text/xml",
            "text/html",
            "text/rtf",
            "application/msword",
            "application/pdf",
        ):
            self["compression"] = "Uncompressed"


class Eyed3Mp3Info(object):
    def __init__(self, filepath):
        mp3 = eyed3.core.load(filepath)
        self._mp3_info = mp3.info

    @property
    def duration(self):
        return self._mp3_info.time_secs

    @property
    def sample_freq(self):
        return self._mp3_info.sample_freq

    @property
    def bit_rate(self):
        if self._mp3_info.bit_rate[0]:
            return None
        return self._mp3_info.bit_rate[1]

    @property
    def layer(self):
        return self._mp3_info.mp3_header.layer

    @property
    def mode(self):
        return self._mp3_info.mode

    @property
    def vbr(self):
        return self._mp3_info.bit_rate[0]


class FFProbeInfo(object):
    """le informazioni raccolte da un file video attraverso avprobe-ffprobe"""

    # TODO: versioni nuove di ffprobe possono fornire l'output in json, usare questo
    def __init__(self, filepath, cmd="ffprobe"):
        self._filepath = filepath
        self._cmd = cmd
        self._collected_info = {}
        self._cur_line = None
        self._proc = self._start_proc()
        self._read()

    @property
    def duration(self):
        return self._collected_info.get("duration")

    @property
    def codec(self):
        return self._collected_info.get("codec")

    @property
    def size(self):
        return self._collected_info.get("size")

    @property
    def aspect_ratio(self):
        return self._collected_info.get("aspect_ratio")

    @property
    def framerate(self):
        return self._collected_info.get("framerate")

    @property
    def bitrate(self):
        return self._collected_info.get("bitrate")

    def _read(self):
        if self._proc is None:
            return

        self._next_line()
        while self._cur_line:
            if self._cur_line.lower().startswith("[format]"):
                self._read_format()
            elif self._cur_line.lower().startswith("[stream"):
                self._read_stream()
            else:
                self._next_line()

        # letto tutto l'output, ffprobe dovrebbe essere terminato
        self._proc.wait()
        if self._proc.returncode != 0:
            logger.warning(
                "ffmpeg exited with %d for %s", self._proc.returncode, self._filepath
            )

    def _read_format(self):
        self._next_line()
        while True:
            m = re.match(r"^duration=(.*)", self._cur_line)
            if m:
                self._collected_info["duration"] = m.group(1).strip()

            m = re.match(r'^bit_rate=(.*)"', self._cur_line)
            if m:
                self._collected_info["bitrate"] = m.group(1).strip()

            elif not self._cur_line or self._cur_line.startswith("["):
                return
            self._next_line()

    def _read_stream(self):
        stream_type = None
        codec = None
        width = None
        height = None
        aspect_ratio = None
        framerate = None

        self._next_line()
        while True:
            m = re.match(r"^codec_type=(.*)", self._cur_line)
            if m:
                stream_type = m.group(1).strip()

            m = re.match(r"^codec_name=(.*)", self._cur_line)
            if m:
                codec = m.group(1).strip()
            m = re.match(r"^width=(.*)", self._cur_line)
            if m:
                width = m.group(1).strip()
            m = re.match(r"^height=(.*)", self._cur_line)
            if m:
                height = m.group(1).strip()
            m = re.match(r"^display_aspect_ratio=(.*)", self._cur_line)
            if m:
                aspect_ratio = m.group(1).strip()
            m = re.match("^avg_frame_rate=(.*)", self._cur_line)
            if m:
                framerate = m.group(1).strip()
                m = re.match(r"(\d+)/(\d+)", framerate)
                if m and int(m.group(2)):
                    framerate = str(int(m.group(1)) // int(m.group(2)))

            if not self._cur_line or self._cur_line.startswith("["):
                break
            self._next_line()

        if stream_type == "video":
            if codec:
                self._collected_info["codec"] = codec
            if width and height:
                self._collected_info["size"] = "%sx%s" % (width, height)
            if aspect_ratio:
                # aspect_ratio ha un "\" da levare
                self._collected_info["aspect_ratio"] = aspect_ratio.replace("\\", "")
            if framerate:
                framerate = re.sub("/1$", "", framerate)
                self._collected_info["framerate"] = framerate

    def _start_proc(self):
        # fa partire e ritorna il processo ffmpeg ritorna None se non è partito
        args = (
            self._cmd,
            "-v",
            "quiet",
            "-show_format",
            "-show_streams",
            self._filepath,
        )
        # TODO: hide prompt on windows
        try:
            proc = subprocess.Popen(args, stdout=subprocess.PIPE, text=True)
        except OSError:
            logger.warning("can't exec %s", self._cmd)
            return None

        return proc

    def _next_line(self):
        self._cur_line = self._proc.stdout.readline()
