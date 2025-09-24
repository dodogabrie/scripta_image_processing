# -*- coding: utf-8 -*-

"""contiene gli strumenti di base per l'importazione di risorse"""


import logging
import os
import posixpath
import re

from maglib.utils import mag_wrapper
from maglib.utils.misc import MagResourcePath

logger = logging.getLogger(__package__)


class Resources_directory(object):
    """rappresenta una directory in cui si possono individuare risorse.
    È possibile specificare il path e le estensioni dei file che devono essere
    considerati all'interno della directory
    L'oggetto sa se e quale usage assegnare alle risorse contenute, ed inoltre
    sa il loro gruppo di riferimento, se applicabile al tipo di risorsa.
    Inoltre conosce il path prefisso che avranno i file contenuti in questa
    directory nel mag"""
    def __init__(self, directory, file_extensions, mag_path_prefix,
                 usage=None, rsrc_group=None):
        """:directory: il path della directory con i file
        :file_extensions: lista con le estensioni dei file (senza punto)
        da considerare
        :param str mag_path_prefix: prefisso dei path da inserire nel mag
        dei file trovati in questa directory
        :usage: oggetto Abs_usage per calcolare gli usage
        :rsrc_group: oggetto Rsrc_group per calcolare il gruppo delle risorse
        """
        self._directory = directory
        self._file_extensions = file_extensions
        self._mag_path_prefix = mag_path_prefix

        self._files = self._build_files_list()
        self._usage = usage or Void_usage()
        self._rsrc_group = rsrc_group or Void_group()

    @property
    def resource_files(self):
        """la lista di file trovati della directory"""
        return self._files

    @property
    def dirpath(self):
        """il path della directory"""
        return self._directory

    @property
    def mag_path_prefix(self):
        """il path prefisso che dovranno avere i file in questa directory
        nel mag"""
        return self._mag_path_prefix

    def convert_resource_path(self, resource_path):
        """converte un nome base di un file aggiungendo il prefisso
        self.mag_path_prefix"""
        basename = os.path.basename(resource_path)
        return posixpath.join(self.mag_path_prefix, basename)

    @property
    def usage(self):
        """oggetto Abs_usage per imposare gli usage delle risorse contenute
        in questa directory"""
        return self._usage

    @property
    def group(self):
        """oggetto Resource_group per impostare il gruppo alle risorse
        contenute in questa directory"""
        return self._rsrc_group

    def find_resource(self, bname):
        """cerca una risorsa in base al nome del file senza estensione, e
        la ritorna con l'estensione"""
        left = 0
        right = len(self._files) - 1
        while left <= right:
            mid = int((left + right) / 2)
            mid_bname = os.path.splitext(self._files[mid])[0]
            if bname < mid_bname:
                right = mid - 1
            elif bname > mid_bname:
                left = mid + 1
            else:
                return self._files[mid]
        return None

    def _build_files_list(self):
        try:
            files = os.listdir(self._directory)
        except (IOError, OSError) as exc:
            logger.warn('Impossibile cercare risorse in %s: %s',
                        self._directory, exc)
            return []
        fileslist = []
        for f in files:
            fpath = os.path.join(self._directory, f)
            fext = os.path.splitext(f)[1][1:].lower()
            if os.path.isfile(fpath) and fext in self._file_extensions:
                fileslist.append(f)
            else:
                logger.info('File estraneo %s in %s' % (f, self._directory))
        fileslist.sort()
        return fileslist


class Rsrc_dir_cmp(object):
    """comprende metodi per confrontare i nomi di directory di risorse"""

    @classmethod
    def cmp_dirs(cls, a_name, b_name):
        """confronta i nomi di due sottodirectory al fine di ordinarle"""

        if a_name < b_name:
            return -1
        elif a_name > b_name:
            return 1
        return 0

    @classmethod
    def cmp_img_dirs(cls, a_name, b_name):
        n_cmp = cls._num_cmp(a_name, b_name)
        if n_cmp is not None:
            return n_cmp

        a_weight = cls._dir_weight(a_name)
        b_weight = cls._dir_weight(b_name)
        if a_weight is not None and b_weight is not None:
            return a_weight - b_weight

        return cls.cmp_dirs(a_name, b_name)

    @classmethod
    def _num_cmp(cls, a_name, b_name):
        # confronta se sia a e b nella forma SN, con S stringa e N numero
        a_match = re.match(r'^(.*?)(\d+)$', a_name)
        if a_match:
            b_match = re.match(r'^{}(\d+)$'.format(a_match.group(1)), b_name)
            if b_match:
                return int(a_match.group(2)) - int(b_match.group(1))
        return None  # impossibile effettuare il confronto

    @classmethod
    def _dir_weight(cls, name):
        if re.match('^thumb(nail)?s', name):
            return 0
        if re.match('^jpe?g', name):
            return 10
        if re.match('^png', name):
            return 20
        if re.match('^tiff?', name):
            return 100
        return None


class Abs_usage(object):
    """imposta gli usage per le risorse"""
    def __init__(self, add_if_present=True, overwrite_if_present=False):
        """:param bool add_if_present: se vero, aggiunge gli usage anche
        se la risorsa ne ha già.
        :param bool overwrite_if_present: se vero, sovrascrive gli usage
        presenti
        se entrambi i parametri sono falsi, non viene impostato niente se
        gli usage sono già presenti"""
        if add_if_present and overwrite_if_present:
            raise RuntimeError(
                'please use only add_if_present OR overwrite_if_present')
        self._add_if_present = add_if_present
        self._overwrite_if_present = overwrite_if_present

    def set(self, resource):
        """imposta gli usage per una risorsa"""
        raise NotImplementedError()

    @classmethod
    def _find_usage(self, resource, usage_value):
        """dice la risorsa ha un usage
        :rtype: bool"""
        for usage in resource.usage:
            if usage.value == usage_value:
                return True
        return False

    def _set_usages(self, resource, usages):
        rsrc_path = mag_wrapper.get_resource_filepath(resource)
        if resource.usage: # usage già presenti
            if self._add_if_present:
                pass
            elif self._overwrite_if_present:
                resource.usage.clear()
                logger.debug('removed usages from resource %s', rsrc_path)
            else:
                logger.debug('usages present, not adding')

        for usage in usages:
            if not self._find_usage(resource, usage):
                mag_wrapper.add_resource_usage(resource, usage)
                logger.debug('usage "%s" aggiunto alla risorsa %s',
                             usage, rsrc_path)
            else:
                logger.debug('usage "%s" non aggiunto alla risorsa %s in '
                             'quanto già presente', usage, rsrc_path)


class Void_usage(Abs_usage):
    """non aggiunge nessun usage"""
    def set(self, resource):
        self._set_usages(resource, ())


class Static_usage(Abs_usage):
    """imposta sempre gli stessi usage"""
    def __init__(self, usages, *args, **kwargs):
        super(Static_usage, self).__init__(*args, **kwargs)
        self._usages = usages
    def set(self, resource):
        self._set_usages(resource, self._usages)


class Dirname_usage(Abs_usage):
    """imposta gli usage in base al path in cui è inclusa la risorsa.
    Le espressioni regolari (case insensitive) della mappa vengono matchate
    con i componenti del path della risorsa, a partire dalla sua directory
    e risalendo"""

    DPI_USAGE = 'DPI_USAGE'

    """istanza di Dirname_usage con le impostazioni classiche per gli img
    group"""
    standard = None

    def __init__(self, usage_map, *args, **kwargs):
        """:usage_map: Questo dizionario mappa i nomi delle directory in cui si
        trovano le risorse in una lista di usage;
        oppure in DPI_USAGE, in questo caso chiave (l'espressione regolare)
        deve avere come gruppo un intero che viene usato per capire gli usage"""
        super(Dirname_usage, self).__init__(*args, **kwargs)
        self._usage_map = usage_map
        self._compiled_usage_map = {}
        for regex, usage_spec in self._usage_map.items():
            self._compiled_usage_map[
                re.compile(regex, re.IGNORECASE)] = usage_spec

    def set(self, resource):
        rsrc_path = mag_wrapper.get_resource_filepath(resource)
        dirnames = MagResourcePath.get_dirnames(rsrc_path)
        for dirname in dirnames:
            matched = False
            for pattern in self._compiled_usage_map:
                match = pattern.match(dirname)
                if match:
                    self._set_usage_spec(
                        resource, match, self._compiled_usage_map[pattern])
                    matched = True
            if matched:
                break

    def _set_usage_spec(self, resource, re_match, usage_spec):
        if usage_spec != self.DPI_USAGE:
            self._set_usages(resource, usage_spec)
            return
        try:
            dpi = int(re_match.group(1))
        except (IndexError, ValueError):
            logger.error('no int in DPI_USAGE regex. No usages set')
            return
        if dpi >= 200:
            usage = '2'
        elif dpi >= 50:
            usage = '3'
        else:
            usage = '4'
        self._set_usages(resource, (usage,))

# inizializzo istanza statica fuori dalla classe
Dirname_usage.standard = Dirname_usage(
    {r'^tiff?$': ('1',),
     r'^jpe?g(\d+)$': Dirname_usage.DPI_USAGE,
     r'^jpe?g$': ('2',),
     r'^png$': ('2',),
     r'^thumb(nail)?s$': ('4',)})



class Resource_group(object):
    """imposta il gruppo per le risorse"""
    def __init__(self, groups_node,
                 ovrwrt_present=False, create_missing=False):
        """:resource_group_node: il nodo del mag con i gruppi"""
        self._groups_node = groups_node
        self._ovrwrt_present = ovrwrt_present
        self._create_missing = create_missing

    def set(self, resource):
        """imposta il gruppo per una risorsa"""
        raise NotImplementedError()

    def _set_group(self, resource, group_id):
        rsrc_path = self._get_resource_path(resource)
        if self._resource_has_group(resource) and not self._ovrwrt_present:
            logger.debug('Gruppo non impostato su risorsa '
                         '%s in quanto gruppo già indicato', rsrc_path)
            return
        if not self._group_present(group_id):
            if not self._create_missing:
                return
            logger.debug('Creato gruppo %s', group_id)
            self._create_group(group_id)
        logger.debug('Impostato gruppo "%s" su risorsa %s',
                     group_id, rsrc_path)
        self._set_resource_group(resource, group_id)

    def _resource_has_group(self, resource):
        raise NotImplementedError()

    def _group_present(self, group_id):
        raise NotImplementedError()

    def _create_group(self, group_id):
        raise NotImplementedError()

    def _get_resource_path(self, resource):
        raise NotImplementedError()

    def _set_resource_group(self, resource, group_id):
        raise NotImplementedError()

class Void_group(Resource_group):
    """non imposta nessun gruppo"""
    def __init__(self):
        pass

    def set(self, resource):
        pass

class Static_group(Resource_group):
    """imposta sempre lo stesso gruppo"""
    def __init__(self, group_id, *args, **kwargs):
        """:group_id: il gruppo da impostare"""
        super(Static_group, *args, **kwargs)
        self._group_id = group_id

    def set(self, resource):
        self._set_group(resource, self._group_id)

class Dirname_group(Resource_group):
    """imposta come gruppo uno dei componenti del path della risorsa
    che corrisponde ad uno dei tipi conosciuti"""

    def set(self, resource):
        resource_path = mag_wrapper.get_resource_filepath(resource)
        format_name = MagResourcePath.guess_img_format_from_dirnames(
            resource_path)
        if format_name:
            self._set_group(resource, format_name)
            return


class Img_group(Resource_group):
    """imposta l'img_group per un'immagine"""
    def _resource_has_group(self, resource):
        return mag_wrapper.get_img_imggroup(resource)

    def _group_present(self, group_id):
        return mag_wrapper.get_imggroup(self._groups_node, group_id)

    def _create_group(self, group_id):
        self._groups_node.add_instance().ID.value = group_id

    def _get_resource_path(self, resource):
        return mag_wrapper.get_resource_filepath(resource)

    def _set_resource_group(self, resource, group_id):
        mag_wrapper.set_img_imggroup(resource, group_id)


class Dirname_img_group(Img_group, Dirname_group):
    pass
