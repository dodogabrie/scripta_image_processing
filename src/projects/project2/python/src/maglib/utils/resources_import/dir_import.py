# -*- coding: utf-8 -*-

"""
questo modulo contiene gli importatori di più basso livello


Le derivate di Dir_resources_importer utilizzano Resources_directory e
importano risorse da directory indicate con un path preciso

== esempio con doc ==
pdf = Resources_directory(
    os.path.join(sys.argv[1], 'pdf'),
    ['pdf'], './AAA/pdf/
    Static_usage(['2']))
doc_importer = Dir_docs_importer(metadigit.doc, pdf)
doc_importer.do_import()
=>  <doc><file href="./AAA/pdf/....

== esempio con immagini, con gruppi ==
tiff = Resources_directory(
    os.path.join(sys.argv[1], 'tiff'),
    ['tif'], './BBB/tiff',
    Static_usage(['1']),
    Dirname_img_group(metadigit.gen[0].img_group, create_missing=True))

j300 = Resources_directory(
    os.path.join(sys.argv[1], 'jpeg300'),
    ['jpg', 'jpeg'], './BBB/jpeg300',
    Dirname_usage.standard,
    Dirname_img_group(metadigit.gen[0].img_group, create_missing=True))

img_importer = Dir_images_importer(
    metadigit.img, # nodo img nel mag
    tiff,          # Resource_directory per il formato principale
    [j300]           # directory con in formati alternativi
)
img_importer.do_import()
=> <img imggroupID="tiff"><file href="./BBB/tiff/1.tif">
     <altimg imggroupID="jpeg300"><file href="./BBB/jpeg300/1.jpg"
"""


import logging
import os

from maglib.utils import mag_wrapper
from maglib.utils.misc import MagResourcePath
from maglib.utils.resources_import.core import Rsrc_dir_cmp

logger = logging.getLogger(__name__)


class Dir_resources_importer(object):
    """esegue l'importazione delle risorse di un certo tipo
    da una precisare directory"""
    def __init__(self, rsrc_node, rsrc_dir):
        """:param xmlbase.Element rsrc_node: oggetto delle risorse
        (img, audio ...)
        :param Resource_directory rsrc_dir: la specifica della directory
        con le risorse
        da importare"""
        self._rsrc_node = rsrc_node
        self._rsrc_dir = rsrc_dir
        self._n_imported = 0

    def do_import(self):
        logger.debug('Importazione risorse da %s', self._rsrc_dir.dirpath)
        for filename in self._rsrc_dir.resource_files:
            filepath = os.path.join(self._rsrc_dir.dirpath, filename)
            self._import_resource(filepath)

        logger.info('Importate %d risorse dalla directory %s',
                    self.n_imported, self._rsrc_dir.dirpath)

    @property
    def n_imported(self):
        """il numero di risorse importate all'interno del mag"""
        return self._n_imported

    def _import_resource(self, resource_path):
        resource = self._resource_for_path(resource_path)
        if resource:
            logger.debug(u'risorsa %s non aggiunta, già presente',
                         resource_path)
            added = False
        else:
            resource = self._rsrc_node.add()
            self._n_imported += 1
            added = True
            logger.debug('risorsa %s aggiunta al mag', resource_path)
        self._set_resource(resource, resource_path, added)

    def _set_resource(self, resource, resource_path, added):
        # "configura" una risorsa, se added è True la risorsa è stata
        # appena aggiunta, altrimenti è esistente
        if added:
            mag_wrapper.set_resource_filepath(
                resource, self._rsrc_dir.convert_resource_path(resource_path))
            # self._set_resource_filepath(
            #     resource, self._rsrc_dir.convert_resource_path(resource_path))
        self._rsrc_dir.usage.set(resource)
        self._rsrc_dir.group.set(resource)

    def _resource_for_path(self, filepath):
        # dice se nel mag c'è già un nodo risorsa riferito a filepath
        # la ritorna se presente, altrimenti ritorna None
        filepath = self._rsrc_dir.convert_resource_path(filepath)
        for resource_node in self._rsrc_node:
            if mag_wrapper.get_all_resource_filepath(resource_node) == filepath:
                #if self._get_resource_filepath(resource_node) == filepath:
                return resource_node
        return None


class Dir_docs_importer(Dir_resources_importer):
    """importa i testi da una singola directory all'interno
    dei nodi doc del mag"""


class Dir_ocr_importer(Dir_resources_importer):
    """importa i testi da una singola directory all'interno
    dei nodi ocr del mag"""


class Dir_images_importer(Dir_resources_importer):
    """importa le immagini da una singola directory all'interno
    dei nodi img del mag.
    Per ogni immagine, cerca dei formati alternativi, se si indicano le
    directory alternative nel costruttore"""
    def __init__(self, imgs_node, imgs_dir, alt_imgs_dir=()):
        """:param list[Resource_directory] alt_imgs_dir: directory dove cercare
        formati alternativi per le immagini"""
        super(Dir_images_importer, self).__init__(imgs_node, imgs_dir)
        self._altimg_dirs = alt_imgs_dir

    def _set_resource(self, resource, resource_path, added):
        super(Dir_images_importer, self)._set_resource(
            resource, resource_path, added)
        self._add_altimgs(resource)

    def _add_altimgs(self, img_node):
        # aggiunge le immagini alternative per l'immagine img_node
        img_path = mag_wrapper.get_resource_filepath(img_node)
        img_name = os.path.basename(img_path)
        img_bname = os.path.splitext(img_name)[0]

        for altimgs_dir in self._altimg_dirs:
            altimg_name = altimgs_dir.find_resource(img_bname)
            if not altimg_name:
                continue
            altimg_path = altimgs_dir.convert_resource_path(altimg_name)
            altimg = self._altimg_for_path(img_node, altimg_path)
            if altimg:
                logger.info('Immagine alternativa %s già presente', altimg_path)
                added = False
            else:
                altimg = img_node.altimg.add_instance()
                added = True
                logger.info(
                    'Aggiunta immagine alternativa %s per l\'immagine %s',
                    altimg_path, img_path)
            self._set_altimg(altimg, altimg_path, altimgs_dir, added)
            if added:
                self._reposition_last_altimg(img_node.altimg)

    def _altimg_key(self, altimg):
        img_group = mag_wrapper.get_img_imggroup(altimg)
        if img_group:
            return img_group
        img_path = mag_wrapper.get_resource_filepath(altimg)
        format_name = MagResourcePath.guess_img_format_from_dirnames(img_path)
        return format_name or ''

    def _reposition_last_altimg(self, altimgs_node):
        # una volta inserita l'altimg (come ultima altimg), questo metodo
        # la sposta in modo che l'ordine delle altimg rimanga valido
        altimg = altimgs_node.pop_instance(-1)
        for index, o_altimg in enumerate(altimgs_node):
            if Rsrc_dir_cmp.cmp_img_dirs(
                    self._altimg_key(altimg), self._altimg_key(o_altimg)
            ) > 0:
                altimgs_node.insert(index, altimg)
                break
        else:
            altimgs_node.append(altimg)

    def _set_altimg(self, altimg, altimg_path, altimg_dir, added):
        if added:
            mag_wrapper.set_resource_filepath(
                altimg, altimg_dir.convert_resource_path(altimg_path))

        altimg_dir.usage.set(altimg)
        altimg_dir.group.set(altimg)

    def _altimg_for_path(self, img_node, altimg_path):
        # ritorna il nodo altimg di img_node che ha esattamente il path
        # altimg_path. se non presente, ritorna None
        for altimg in img_node.altimg:
            if mag_wrapper.get_resource_filepath(altimg) == altimg_path:
                return altimg
        return None


class Dir_proxied_resource_importer(Dir_resources_importer):
    """importa le risorse di tipo proxy (audio, video) da una
    singola directory"""
    # TODO: supportare i gruppi di risorse
    _resource_label = ''

    def __init__(self, rsrc_node, rsrc_dir, alt_rsrc_dirs=()):
        """:param list[Resources_directory] alt_rsrc_dirs: dove cercare proxy
        ulteriori a quello principale"""
        super(Dir_proxied_resource_importer, self).__init__(rsrc_node, rsrc_dir)
        self._alt_rsrc_dirs = alt_rsrc_dirs

    def _set_resource(self, resource, resource_path, added):
        if not resource.proxies:
            resource.proxies.add_instance()
        self._set_proxy(
            resource.proxies[0], resource_path, self._rsrc_dir, added)
        self._add_alt_proxies(resource)

    def _set_resource_filepath(self, audio, path):
        # non dovrebbe essere usato, seppure usato dalla madre
        raise NotImplementedError()

    def _add_alt_proxies(self, resource_node):
        # aggiunge i proxy ulteriori al primo in un nodo
        rsrc_path = mag_wrapper.get_all_resource_filepath(resource_node)
        #rsrc_path = self._get_resource_filepath(resource_node)
        bname = os.path.splitext(os.path.basename(rsrc_path))[0]
        for alt_rsrc_dir in self._alt_rsrc_dirs:
            alt_rsrc_name = alt_rsrc_dir.find_resource(bname)
            if not alt_rsrc_name:
                continue
            alt_rsrc_path = alt_rsrc_dir.convert_resource_path(alt_rsrc_name)
            alt_rsrc = self._proxy_for_path(resource_node, alt_rsrc_path)
            if alt_rsrc:
                added = False
                logger.info('proxy %s alternativo %s già presente',
                            self._resource_label, alt_rsrc_path)
            else:
                added = True
                logger.info('Aggiunto proxy alternativo %s per %s',
                            alt_rsrc_path, rsrc_path)
                alt_rsrc = resource_node.proxies.add_instance()
            self._set_proxy(alt_rsrc, alt_rsrc_path, alt_rsrc_dir, added)
            if added:
                self._reposition_last_proxy(resource_node)

    def _set_proxy(self, audio_proxy, audio_path, audio_dir, added):
        # imposta le caratteristiche su un proxy audio
        mag_wrapper.set_resource_filepath(
            audio_proxy, audio_dir.convert_resource_path(audio_path))
        audio_dir.usage.set(audio_proxy)

    def _proxy_for_path(self, audio_node, path):
        #proxy_path = self._convert_resource_path(path)
        for proxy in audio_node.proxies:
            if mag_wrapper.get_resource_filepath(proxy) == path:
                return proxy
        return None

    def _reposition_last_proxy(self, audio_node):
        # TODO: implementare per avere un ordinamento fra i proxy trovati
        # in alt_audio_dirs
        pass


class Dir_audio_importer(Dir_proxied_resource_importer):
    """importa gli audio da una singola directory all'interno dei nodi
    audio del mag"""
    _label = 'audio'


class Dir_video_importer(Dir_proxied_resource_importer):
    """importa i video da una singola directory all'interno dei nodi video
    del mag"""
    _label = 'video'
