# -*- coding: utf-8 -*-

"""questo modulo contiene importatori che forniscono un livello di astrazione
sopra quelli di dir_import, permettendo facilmente di importare più
sottodirectory dall'interno di una singola directory (la directory del mag)

Le derivate di Resources_importer utilizzano Resources_dir_spec e quindi
importano le risorse attraverso una directory base e sottodirectory specificata
come glob-style

== import ocr ==
ocr_dir_spec = Resources_dir_spec(
     'pdf', ['pdf'], usage=Static_usage(['2']))
ocr2_dir_spec = Resources_dir_spec(
     'txt', ['txt', 'doc'], usage=Static_usage(['2']))
importer = Ocr_imporer(metadigit.ocr, '/srv/A',
                       [ocr_dir_spec, ocr2_dir_spec])
=><ocr><file href="./A/pdf/1.pdf"/>
  <ocr><file href="./A/txt/1.txt"/>

tiff = Resources_dir_spec(
    'tiff', ('tif',), Static_usage(['1']),
    Dir_img_group(metadigit.gen[0].img_group, create_missing=True))
jpeg = Resources_dir_spec(
    'jpeg*',
    ('jpg', 'jpeg'),
    Dpi_dirname_usage({'^jpe?g(\\d+)$': 'DPI_USAGE'}),
    Dir_img_group(metadigit.gen[0].img_group, create_missing=True))
img_importer = Images_importer(metadigit.img, sys.argv[1], [tiff], [jpeg])
img_importer.do_import()"""

import glob
import logging
import os
import posixpath
from functools import cmp_to_key

from maglib.utils.resources_import.core import (Resources_directory,
                                                Rsrc_dir_cmp)
from maglib.utils.resources_import.dir_import import (Dir_audio_importer,
                                                      Dir_docs_importer,
                                                      Dir_images_importer,
                                                      Dir_ocr_importer,
                                                      Dir_video_importer)

logger = logging.getLogger(__package__)
join = os.path.join


class Resources_dir_spec(object):
    """permette di specificare una serie di sottodirectory comprese nella
    directory del mag, attraverso una stringa glob che può esprimere anche
    più livelli di profondità
    Da questo viene custruita una lista di Resources_directory"""
    def __init__(self, subdir_glob, file_extensions,
                 usage=None, rsrc_group=None):
        """:param str subdir_spec: path, eventualmente con glob, che specifica
        le sottodirectory delle risorse
        :param list[str] file_extensions: list di estensioni di file da
        considerare
        :usage: oggetto Abs_usage per calcolare gli usage
        :rsrc_group: oggetto Rsrc_group per calcolare il gruppo delle risorse"""
        self._subdir_glob = subdir_glob
        self._file_extensions = file_extensions
        self._usage = usage
        self._rsrc_group = rsrc_group

    @property
    def subdir_glob(self):
        return self._subdir_glob

    @property
    def file_extensions(self):
        return self._file_extensions

    @property
    def usage(self):
        return self._usage

    @property
    def rsrc_group(self):
        return self._rsrc_group


class Resources_importer(object):
    """Importa un tipo di risorse da una serie di directory contenute nella
    directory principale del mag"""
    def __init__(self, resources_node, basedir, dirs_specs,
                 dotslash=True, extra_path_levels=1):
        # TODO: permettere di inserire path assoluti
        """:param resources_node: il nodo delle risorse nel mag
        :param str basedir: la directory principale del mag
        :dirs_specs: lista di Resources_dir_spec per individuare le directory
        da cui importare le risorse
        :param bool dotslash: se vero, inserisci ./ davanti ai path relativi
        inseriti nel mag
        :param int extra_path_levels: di quanti livelli salire
        dalla directory basedir per esprimere i path del mag"""
        self._resources_node = resources_node
        self._basedir = basedir
        self._dotslash = dotslash
        self._extra_path_levels = extra_path_levels

        self._resources_dirs = self._build_resources_dirs(dirs_specs)
        self._n_imported = 0

    def do_import(self):
        """esegue l'importazione"""
        logger.info('Individuate %d directory per l\'importazione in %s',
                    len(self._resources_dirs), self._basedir)
        for dIr in self._resources_dirs:
            importer = self._build_dir_importer(dIr)
            importer.do_import()
            self._n_imported += importer.n_imported
        logger.debug('Importate %d risorse', self.n_imported)

    @property
    def n_imported(self):
        """ritorna il numero di risorse importate"""
        return self._n_imported

    def _build_resources_dirs(self, dirs_specs):
        resources_dirs = []
        for dir_spec in dirs_specs:
            for subdir in glob.glob(join(self._basedir, dir_spec.subdir_glob)):
                path = self._build_resources_dir_mag_path(subdir)
                rsrc_dir = Resources_directory(
                    subdir, dir_spec.file_extensions, path,
                    dir_spec.usage, dir_spec.rsrc_group)
                resources_dirs.append(rsrc_dir)
        resources_dirs.sort(key= lambda d: d.dirpath)
        return resources_dirs

    def _build_resources_dir_mag_path(self, subdir_path):
        # costruisce il path che corrisponde al path di una directory nel mag
        # path relativo della sottodirectory di risorse,
        # a partire dalla directory base
        path = os.path.relpath(subdir_path, self._basedir)
        # aggiungo i livelli superiori richiesti
        parent = os.path.normpath(self._basedir)
        for c in range(self._extra_path_levels):
            parent, d = os.path.split(parent)
            path = posixpath.join(d, path)
        path = posixpath.normpath(path) # normalizzo

        # eventualmente aggiungo dotslash, DOPO normpath sennò lo rimuove
        # ./ non aggiunto comunque se la directory base è già "." !
        if self._dotslash and path != '.':
            path = posixpath.join('.', path)
        return path

    def _build_dir_importer(self, resources_dir):
        raise NotImplementedError()


class Docs_importer(Resources_importer):
    def _build_dir_importer(self, resources_dir):
        return Dir_docs_importer(self._resources_node, resources_dir)


class Ocr_importer(Resources_importer):
    def _build_dir_importer(self, resources_dir):
        return Dir_ocr_importer(self._resources_node, resources_dir)


class Images_importer(Resources_importer):
    def __init__(self, resources_node, basedir, dirs_specs, altimgs_dirs_specs,
                 dotslash=True, extra_path_levels=1):
        """:altimgs_dirs_specs: lista di Resources_dir_spec per individuare le
        directory dei formati alternativi"""
        super(Images_importer, self).__init__(
            resources_node, basedir, dirs_specs, dotslash, extra_path_levels)

        self._altimgs_dirs = self._build_resources_dirs(altimgs_dirs_specs)

    def _build_dir_importer(self, resources_dir):
        return Dir_images_importer(
            self._resources_node, resources_dir, self._altimgs_dirs)

    @classmethod
    def _cmp_img_dirs(self, a, b):
        return Rsrc_dir_cmp.cmp_img_dirs(
            os.path.basename(a.dirpath), os.path.basename(b.dirpath)
        )

    def _build_resources_dirs(self, dirs_specs):
        resource_dirs = super(Images_importer, self)._build_resources_dirs(
            dirs_specs)
        resource_dirs.sort(key=cmp_to_key(self._cmp_img_dirs), reverse=True)
        return resource_dirs


class Audio_importer(Resources_importer):
    def __init__(self, resources_node, basedir, dirs_spec,
                 alt_proxies_dirs_specs=(), dotslash=True, extra_path_levels=1):
        """:alt_proxies_dirs_specs: lista di Resources_dir_spec per i
        proxies alternativi"""
        super(Audio_importer, self).__init__(
            resources_node, basedir, dirs_spec, dotslash, extra_path_levels)
        self._alt_proxies_dirs = self._build_resources_dirs(alt_proxies_dirs_specs)

    def _build_dir_importer(self, resources_dir):
        return Dir_audio_importer(
            self._resources_node, resources_dir, self._alt_proxies_dirs)


class Video_importer(Resources_importer):
    def __init__(self, resources_node, basedir, dirs_spec,
                 alt_proxies_dirs_specs=(), dotslash=True, extra_path_levels=1):
        super(Video_importer, self).__init__(
            resources_node, basedir, dirs_spec, dotslash, extra_path_levels)
        self._alt_proxies_dirs = self._build_resources_dirs(
            alt_proxies_dirs_specs)

    def _build_dir_importer(self, resources_dir):
        return Dir_video_importer(
            self._resources_node, resources_dir, self._alt_proxies_dirs)
