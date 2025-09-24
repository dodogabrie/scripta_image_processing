# -*- coding: utf-8 -*-

"""questo modulo contiene gli importatori di più alto livello
Si specificano le opzioni con una derivata di ImportOptions, poi l'importatore
ha bisogno solo del path e del mag"""


import logging
import re

from maglib.utils.mag_wrapper import (
    AudioSort,
    DocsSort,
    ImagesSort,
    OcrSort,
    SeqNsReset,
    VideoSort,
)
from maglib.utils.resources_import.core import (
    Dirname_img_group,
    Dirname_usage,
    Static_usage,
)
from maglib.utils.resources_import.spec_import import (
    Audio_importer,
    Docs_importer,
    Images_importer,
    Ocr_importer,
    Resources_dir_spec,
    Video_importer,
)

logger = logging.getLogger(__package__)


class ImportOptions(object):
    """opzioni per effettuare l'importazione di risorse"""
    def __init__(self, subdirs, sort=False, dotslash=True,
                 extra_path_levels=1):
        """:param list[str] subdirs: lista di path (glob) per le sottodirectory
        in cui cercare le risorse
        :param bool sort: se vero, ordina tutte le risorse dopo
        l'importazione
        :param bool dotslash: se vero, inserisci ./ davanti ai path relativi
        inseriti nel mag
        :param int extra_path_levels: di quanti livelli salire
        dalla directory basedir per esprimere i path del mag"""
        self._subdirs = subdirs
        self._sort = sort
        self._dotslash = dotslash
        self._extra_path_levels = extra_path_levels

    @property
    def subdirs(self):
        return self._subdirs
    @property
    def sort(self):
        return self._sort
    @property
    def dotslash(self):
        return self._dotslash
    @property
    def extra_path_levels(self):
        return self._extra_path_levels

    def as_dict(self):
        """ritorna una rappresentazione in dizionario delle opzioni"""
        return dict((attr, getattr(self, attr)) for attr in (
            'subdirs', 'sort', 'dotslash', 'extra_path_levels'))


class ImageImportOptions(ImportOptions):
    """opzioni per effettuare l'importazione di immagini"""
    def __init__(self, alt_subdirs=(), create_groups=False,
                 *args, **kwargs):
        """:param list[str] alt_dirs: lista di path (glob) per le
        sottosottodirectory per i formati alternativi
        :param bool create_groups: se vero, imposta anche gli imggroup
        che non esistono, aggiungendoli in gen"""
        super(ImageImportOptions, self).__init__(*args, **kwargs)
        self._alt_subdirs = alt_subdirs
        self._create_groups = create_groups

    @property
    def alt_subdirs(self):
        return self._alt_subdirs
    @property
    def create_groups(self):
        return self._create_groups

    def as_dict(self):
        d = super(ImageImportOptions, self).as_dict()
        d['alt_subdirs'] = self.alt_subdirs
        d['create_groups'] = self.create_groups
        return d


class DocOcrImportOptions(ImportOptions):
    """opzioni per doc e ocr"""
    _def_extensions = ('rtf', 'doc', 'txt', 'xml', 'html', 'pdf')

    def __init__(self, usages=('3',), extensions=_def_extensions,
                 *args, **kwargs):
        """:param list[str] usages: lista degli usages da inserire
        :param list[str] extensions: estensioni da considerare per i file"""
        super(DocOcrImportOptions, self).__init__(*args, **kwargs)
        self._usages = usages
        self._extensions = extensions

    @property
    def usages(self):
        return self._usages

    @property
    def extensions(self):
        return self._extensions

    def as_dict(self):
        d = super(DocOcrImportOptions, self).as_dict()
        d['usages'] = self._usages
        d['extensions'] = self._extensions
        return d


class DocImportOptions(DocOcrImportOptions):
    """opzioni per effettuare l'importazione di doc"""

class OcrImportOptions(DocOcrImportOptions):
    """opzioni per effettuare l'importazione di ocr"""



class AudioVideoImportOptions(ImportOptions):
    def __init__(self, alt_subdirs=(), usages=(), extensions=(),
                 *args, **kwargs):
        """:param list[str] usages: lista degli usages da inserire
        :param list[str] extensions: estensioni da considerare per i file"""
        super(AudioVideoImportOptions, self).__init__(*args, **kwargs)
        self._alt_subdirs = alt_subdirs
        self._extensions = extensions
        self._usages = usages

    @property
    def alt_subdirs(self):
        return self._alt_subdirs
    @property
    def extensions(self):
        return self._extensions
    @property
    def usages(self):
        return self._usages

    def as_dict(self):
        d = super(AudioVideoImportOptions, self).as_dict()
        d['alt_subdirs'] = self._alt_subdirs
        d['usages'] = self._usages
        d['extensions'] = self._extensions
        return d


class VideoImportOptions(AudioVideoImportOptions):
    _def_extensions = ('wmv', 'avi', 'mpeg', 'mpg', 'mp4', 'vob', 'mov')
    def __init__(self, extensions=_def_extensions, *args, **kwargs):
        super(VideoImportOptions, self).__init__(
            extensions=extensions, *args, **kwargs)


class AudioImportOptions(AudioVideoImportOptions):
    _def_extensions = ('wav', 'mp3', 'mid', 'midi')
    def __init__(self, extensions=_def_extensions, *args, **kwargs):
        super(AudioImportOptions, self).__init__(
            extensions=extensions, *args, **kwargs)


class ImportRunner(object):
    """effettua una importazione"""
    def __init__(self, metadigit, mag_path, import_opts):
        self._metadigit = metadigit
        self._mag_path = mag_path
        self._msg = ''

        self._import_opts = import_opts
        self._importer = self._build_importer()

    def run(self):
        """esegue l'importazione"""
        self._importer.do_import()
        self._msg += 'Eseguita importazione di %d %s nel mag' % (
            self._importer.n_imported, self.resources_label)
        if self._import_opts.sort:
            self._do_sort()
        self._set_seq_ns()
        logger.debug(self.message.replace('\n', '   '))

    @property
    def message(self):
        return self._msg

    @property
    def resources_label(self):
        raise NotImplementedError()

    def _do_sort(self):
        raise NotImplementedError()

    def _set_seq_ns(self):
        raise NotImplementedError()

    def _build_importer(self):
        # costruisce il maglib.utils.resources_importer.Resources_importer
        # da usare
        raise NotImplementedError()


class ImageImportRunner(ImportRunner):
    """effettua l'importazione sull immagini"""
    resources_label = 'immagini'

    # mappatura nome subdir -> estensioni da cercare
    _extensions_map = (
        (re.compile(r'^tiff?$'), ('tif', 'tiff')),
        (re.compile(r'^jpe?g.*$'), ('jpg', 'jpeg')),
        (re.compile(r'^thumb(nail)?s$'), ('jpg', 'jpeg', 'png')),
        (re.compile(r'^png$'), ('png',)),
    )
    # estensioni considerate per una sottodirectory sconosciuta
    _default_extensions = ('tif', 'tiff', 'jpg', 'jpeg', 'png', 'djvu')

    def _build_importer(self):
        if not self._metadigit.gen:
            self._metadigit.gen.add_instance()

        usage = Dirname_usage.standard

        img_group = Dirname_img_group(
            self._metadigit.gen[0].img_group,
            create_missing=self._import_opts.create_groups)

        main_dirs_specs = [
            Resources_dir_spec(d, self._guess_extensions(d), usage, img_group)
            for d in self._import_opts.subdirs]
        alt_dirs_specs = [
            Resources_dir_spec(d, self._guess_extensions(d), usage, img_group)
            for d in self._import_opts.alt_subdirs]

        return Images_importer(
            self._metadigit.img, self._mag_path,
            main_dirs_specs, alt_dirs_specs, self._import_opts.dotslash,
            self._import_opts.extra_path_levels)

    def _guess_extensions(self, dirname):
        # lista di estensioni cercate per una sottodirectory
        for dir_regex, extensions in self._extensions_map:
            if dir_regex.match(dirname):
                return extensions
        return self._default_extensions

    def _do_sort(self):
        ImagesSort(self._metadigit.img).sort_by_filename()
        self._msg += '\nImmagini riordinate'

    def _set_seq_ns(self):
        SeqNsReset.on_resource_node(
            self._metadigit.img, 'img', self._metadigit.stru)


class DocOcrImportRunner(ImportRunner):
    # classe astratta base per ocr e doc
    def _read_dir_specs(self):
        # legge dir specs dalle opzioni
        dir_specs = []
        for subdir in self._import_opts.subdirs:
            dir_specs.append(Resources_dir_spec(
                subdir, self._import_opts.extensions,
                Static_usage(self._import_opts.usages)))
        return dir_specs


class DocImportRunner(DocOcrImportRunner):
    resources_label = 'documenti'
    def _build_importer(self):
        dir_specs = self._read_dir_specs()
        return Docs_importer(
            self._metadigit.doc, self._mag_path, dir_specs,
            self._import_opts.dotslash, self._import_opts.extra_path_levels)

    def _do_sort(self):
        DocsSort(self._metadigit.doc).sort_by_filename()
        self._msg += '\nDocumenti riordinati'

    def _set_seq_ns(self):
        SeqNsReset.on_resource_node(
            self._metadigit.doc, 'doc', self._metadigit.stru)

class OcrImportRunner(DocOcrImportRunner):
    resources_label = 'documenti OCR'
    def _build_importer(self):
        dir_specs = self._read_dir_specs()
        return Ocr_importer(
            self._metadigit.ocr, self._mag_path, dir_specs,
            self._import_opts.dotslash, self._import_opts.extra_path_levels)

    def _do_sort(self):
        OcrSort(self._metadigit.ocr).sort_by_filename()
        self._msg += '\nDocumenti OCR riordinati'

    def _set_seq_ns(self):
        SeqNsReset.on_resource_node(
            self._metadigit.ocr, 'ocr', self._metadigit.stru)


class VideoImportRunner(ImportRunner):
    resources_label = 'Video'
    def _do_sort(self):
        VideoSort(self._metadigit.video).sort_by_filename()
        self._msg += '\nVideo riordinati'

    def _set_seq_ns(self):
        SeqNsReset.on_resource_node(
            self._metadigit.video, 'video', self._metadigit.stru)

    def _build_importer(self):
        opts = self._import_opts
        dir_specs = [
            Resources_dir_spec(
                subdir, opts.extensions, Static_usage(opts.usages))
            for subdir in opts.subdirs]
        alt_dir_specs = [
            Resources_dir_spec(
                subdir, opts.extensions, Static_usage(opts.usages))
            for subdir in opts.alt_subdirs]
        return Video_importer(
            self._metadigit.video, self._mag_path, dir_specs,
            alt_dir_specs, opts.dotslash, opts.extra_path_levels)


class AudioImportRunner(ImportRunner):
    resources_label = 'Audio'
    def _do_sort(self):
        AudioSort(self._metadigit.audio).sort_by_filename()
        self._msg += '\nAudio riordinati'

    def _set_seq_ns(self):
        SeqNsReset.on_resource_node(
            self._metadigit.audio, 'audio', self._metadigit.stru)

    def _build_importer(self):
        opts = self._import_opts
        dir_specs = [
            Resources_dir_spec(
                subdir, opts.extensions, Static_usage(opts.usages))
            for subdir in opts.subdirs]
        alt_dir_specs = [
            Resources_dir_spec(
                subdir, opts.extensions, Static_usage(opts.usages))
            for subdir in opts.alt_subdirs]
        return Audio_importer(
            self._metadigit.audio, self._mag_path, dir_specs,
            alt_dir_specs, opts.dotslash, opts.extra_path_levels)
