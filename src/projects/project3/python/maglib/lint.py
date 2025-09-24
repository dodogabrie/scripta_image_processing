# -*- coding: utf-8 -*-

"""modulo per controllare la correttezza di un mag"""

import hashlib
import os
import re
import stat

from lxml import etree
from PIL import Image

from maglib import Metadigit
from maglib.xmlbase import Simple_element_instance


class MagLint(object):
    tests = ()

    def __init__(self, tests=(), stop_on_first_fail=False):
        """:tests: test da eseguire sul mag
        :stop_on_first_fail: se vero, interrompi al primo test fallito"""
        self._tests = tests or self.tests
        self._stop_on_first_fail = stop_on_first_fail

    def test(self, metadigit):
        """esegue la validazione del mag :metadigit:"""
        errors = []
        for test in self._tests:
            target = self._get_test_target(metadigit, test)
            if target is None:
                errors.append(MagTestError(
                        test.__class__, metadigit,
                        'Impossibile trovare il target'))
                continue

            test_errors = test(target)
            errors.extend(test_errors)
            if test_errors and self._stop_on_first_fail:
                break

        return errors

    def _get_test_target(self, metadigit, test):
        # ottiene il target (nodo maglib) per un test
        # :test: MagTest
        # :metadigit: Metadigit
        if not test.target:
            return metadigit
        try:
            return eval('metadigit.%s' % test.target)
        except Exception as exc:
            return None


class MagTest(object):
    """un test di correttezza su di un nodo del mag"""
    # elemento su cui effettuare il test, come stringa a partire da metadigit
    target = ''

    def __call__(self, mag_obj):
        """esegue il testo su :mag_obj: e ritorna gli errori"""
        raise NotImplementedError()

    def _build_error(self, mag_obj, msg):
        return MagTestError(self.__class__, mag_obj, msg)


class IterMagTest(MagTest):
    """un test che scorre le istanze di un nodo"""
    def __init__(self, stop_on_first_fail=False):
        """:stop_on_first_fail: se vero, interrompi il test quando si fallisce
        per la prima volta su un istanza del nodo"""
        self._stop_on_first_fail = stop_on_first_fail

    def __call__(self, mag_obj):
        # do NOT override
        errors = []
        for obj_instance in mag_obj:
            instance_errors = self._call_on_instance(obj_instance)
            if instance_errors:
                errors.extend(instance_errors)
                if self._stop_on_first_fail:
                    break
        return errors

    def _call_on_instance(self, mag_obj):
        raise NotImplementedError()


class MagTestError(object):
    """un errore avvenuto testando un mag"""
    def __init__(self, TestClass, mag_obj, msg):
        self._TestClass = TestClass
        self._mag_obj = mag_obj
        self._msg = msg

    @property
    def test(self):
        """la classe del test che è fallito"""
        return self._TestClass

    def __unicode__(self):
        return u'Test %s%s' % (
            self._TestClass.__name__,
            ': %s' % (self._msg,) if self._msg else '')

    def __str__(self):
        return self.__unicode__().encode('utf-8')


class SchemaTest(MagTest):
    """testa il mag nei confronti dello schema xsd"""
    # locazione di default dello schema mag dentro la directory della libreria
    DEF_SCHEMA_PATH = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 'mag_schema', 'metadigit.xsd')
    # test su tutto metadigit
    target = ''

    def __init__(self, schema_path=None):
        self._schema_path = schema_path or self.DEF_SCHEMA_PATH
        try:
            self._schema = etree.XMLSchema(file=self._schema_path)
        except etree.XMLSchemaParseError as exc:
            self._schema = None

    def __call__(self, mag_obj):
        # :mag_obj: Metadigit
        if not self._schema:
            return [self._build_error(
                mag_obj, 'Load of xsd schema %s failed' % self._schema_path)
            ]

        xml = mag_obj.as_xml()
        if not self._schema.validate(xml):
            errors = self._schema.error_log
            return [self._build_error(mag_obj, errors)]
        return []


class ImgGroupsTest(MagTest):
    """testa gli img group nella sezione generale del mag"""
    target = 'gen[0].img_group'

    def __init__(self, names):
        """:names: i nomi degli img group che devono essere presenti nel mag"""
        self._names = names

    def __call__(self, imggroup_node):
        if len(imggroup_node) != len(self._names):
            err_msg = 'Il mag non ha %d img_group' % len(self._names)
            return [self._build_error(imggroup_node, err_msg)]

        errors = []
        for i, imgroup in enumerate(imggroup_node):
            if imgroup.ID.value != self._names[i]:
                err_msg = 'L\'img group %d non si chiama %s' % (
                    i, self._names[i])
                errors.append(self._build_error(imggroup_node, err_msg))
        return errors


class FieldsTest(MagTest):
    """testa dei campi semplici di un nodo del mag"""
    def __init__(self, field_values):
        """field_values è un dizionario è nella forma nome-campo:valore-campo
        I valori possono essere passati come
        - None (test a successo se il campo non è presente nel mag
        - stringhe (test ha successo se c'è uguaglianza)
        - liste (test ha successo se c'è uguaglianza con uno degli elementi
          nella lista)
        - re.RegexObject (test ha successo se l' espressione regolare
        corrisponde"""
        self._field_values = field_values

    def __call__(self, mag_object):
        errors = []
        for field, value in self._field_values.items():
            field_error = self._test_field(mag_object, field, value)
            if field_error:
                errors.append(field_error)
        return errors

    def _test_field(self, mag_object, field, value):
        try:
            mag_field = getattr(mag_object, field)
        except AttributeError:
            err_msg = "L'elemento %s non ha l\'elemento %s, impossibile " % (
                    mag_object.get_simple_name(), field) + 'eseguire il test'
            return self._build_error(mag_object, err_msg)

        if not issubclass(mag_field.Instance, Simple_element_instance) or \
                mag_field.max_occurrences != 1:
            err_msg = u'L\'elemento %s non è semplice, ' % field + \
                                'impossibile eseguire il test'
            return self._build_error(mag_object, err_msg)

        if value is None:
            if mag_field:
                return self._build_error(
                    mag_object, 'L\'elemento %s specifica un valore' % field)


        if not mag_field:
            return self._build_error(
                mag_object, 'L\'elemento %s non ha un valore' % field)

        mag_field_value = mag_field[0].value or ''

        if hasattr(value, 'match') and hasattr(value, 'pattern'):
            # re.RegexObject
            if not value.match(mag_field_value):
                return self._build_error(
                    mag_object,
                    u'Il valore dell\'elemento %s ("%s") non ' % (
                        mag_field.name, mag_field_value) + 'corrisponde all\''
                    'espressione regolare "%s"' % value.pattern)
        elif isinstance(value, basestring):
            if mag_field_value != value:
                return self._build_error(
                    mag_object,
                    u'Il valore dell\'elemento %s non è "%s"' % (
                        mag_field.name, value))
        elif hasattr(value, '__iter__'):
            if not mag_field_value in value:
                return self._build_error(
                    mag_object,
                    u'Il valore dell\'elemento %s non è compreso in %s' % (
                        mag_field.name, value))
        else:
            raise ValueError('Invalid field value %s' % value)


class GenTest(FieldsTest):
    """testa i valori nella sezione gen del mag"""
    target = 'gen[0]'


class LibraryTest(FieldsTest):
    target = 'bib[0].holdings[0]'
    def __init__(self, library_value):
        super(LibraryTest, self).__init__({'library': library_value})


class VolDirContentsTest(MagTest):
    """controlla che il contenuto della directory di un volume sia espresso
    nel mag"""
    def __init__(self, voldir):
        """:voldir: path che contiene le immagini del mag"""
        self._voldir = voldir

    def __call__(self, metadigit):
        voldirname = os.path.basename(self._voldir)
        mag_resources = self._find_mag_resources(metadigit)
        try:
            subdirs = os.listdir(self._voldir)
        except OSError as exc:
            return [self._build_error(
                metadigit,
                'manca directory attesa del mag %s' % voldirname)]
        subdirs.sort(key=self._subdir_key)
        errors = []
        for subdir in subdirs:
            if not re.match(r'^(tiff|master|jpeg\d+|thumb(nail)?s|pdf|txt)$', subdir):
                errors.append(self._build_error(
                    metadigit, 'contenuto %s sconosciuto' % subdir))
                continue
            for f in os.listdir(os.path.join(self._voldir, subdir)):
                path_in_mag = './%s/%s/%s' % (voldirname, subdir, f)
                if not path_in_mag in mag_resources:
                    errors.append(self._build_error(
                            metadigit, 'file %s non nel mag' % path_in_mag))
        return errors

    def _find_mag_resources(self, metadigit):
        resources = set()
        for img in metadigit.img:
            path = img.file[0].href.value
            resources.add(path)
            for altimg in img.altimg:
                path = altimg.file[0].href.value
                resources.add(path)
        for ocr in metadigit.ocr:
            path = ocr.file[0].href.value
            resources.add(path)
        return resources

    def _subdir_key(self, subdir):
        if subdir == 'tiff':
            return -1
        if subdir.startswith('jpeg'):
            return int(subdir[4:])
        return 9999


class FileMixin(object):
    def __init__(self, basepath):
        self._basepath = basepath

    def _get_resource_path(self, resource):
        if not resource.file or not resource.file[0].href.value:
            return None
        return os.path.join(self._basepath, resource.file[0].href.value)


class FilePresenceMixin(FileMixin):
    def _call_on_resource(self, resource):
        fpath = self._get_resource_path(resource)
        if not fpath:
            return self._build_error(resource, 'non ha un file')
        if not os.path.isfile(fpath):
            return self._build_error(resource, 'il file non esiste')


class FilesizeMixin(FileMixin):
    def _call_on_resource(self, rsrc):
        fpath = self._get_resource_path(rsrc)
        if not fpath:
            return self._build_error(rsrc, 'nessun filename')
        if not rsrc.filesize.get_value():
            return self._build_error(rsrc, 'nessun filesize nel mag')
        try:
            size_in_mag = int(rsrc.filesize.get_value())  # mancano controlli
        except ValueError:
            return self._build_error(rsrc, 'filesize nel mag errato: %s' % (
                    rsrc.filesize.get_value()))

        try:
            file_size = os.stat(fpath)[stat.ST_SIZE]
        except OSError:
            return self._build_error(rsrc, 'stat del file fallito')
        if size_in_mag != file_size:
            return self._build_error(rsrc, 'dimensioni file errate')
        return None


class Md5Mixin(FileMixin):
    _BUFSIZE = 8192 * 1024

    def _call_on_resource(self, rsrc):
        fpath = self._get_resource_path(rsrc)
        mag_md5 = rsrc.md5.get_value()
        try:
            file_md5 = self._file_md5(fpath)
        except IOError as exc:
            return self._build_error(rsrc, 'non posso calcolare md5: %s' % exc)
        if mag_md5 != file_md5:
            return self._build_error(rsrc, 'md5 errato')
        return None

    def _file_md5(self, fpath):
        hasher = hashlib.md5()
        f = open(fpath, 'rb')
        buf = f.read(self._BUFSIZE)
        while buf:
            hasher.update(buf)
            buf = f.read(self._BUFSIZE)
        return hasher.hexdigest()


class ImgTest(IterMagTest):
    """test su le immagini"""
    target = 'img'

    def _build_error(self, mag_obj, msg):
        msg = '%s: %s' % (mag_obj.file[0].href.value, msg)
        return super(ImgTest, self)._build_error(mag_obj, msg)

    def _call_on_instance(self, img):
        errors = []
        for img in [img] + list(img.altimg):
            err = self._call_on_resource(img)
            if err:
                errors.append(err)
                if self._stop_on_first_fail:
                    break
        return errors


class FilenameReMixin(object):
    def __init__(self, regex):
        self._regex_string = regex
        self._regex = re.compile(self._regex_string)

    def _call_on_resource(self, resource):
        if not resource.file or not resource.file[0].href.value:
            return self._build_error(resource, 'non ha nessun filename')
        filename = os.path.basename(resource.file[0].href.value)
        if not self._regex.match(filename):
            return self._build_error(
                resource,
                'il filename non corrisponde a %s' % self._regex_string)


class ImgFilenameTest(FilenameReMixin, ImgTest):
    """controlla che i nomi di file delle immagini corrispondano ad una
    espressione regolare"""
    def __init__(self, regex, stop_on_first_fail=False):
        FilenameReMixin.__init__(self, regex)
        ImgTest.__init__(self, stop_on_first_fail)


class ImgTestGroups(ImgTest):
    """testa l'img group delle immagini e dei suoi formati alternativi"""
    def __init__(self, groups, stop_on_first_fail=False):
        """:img_groups: i nomi degli img group che deve avere ogni immagine.
        Il primo imggroup è dell'immagine primaria, i seguenti sono dei
        formati alternativi"""
        super(ImgTestGroups, self).__init__(stop_on_first_fail)
        self._groups = groups

    def _call_on_instance(self, img):
        errors = []
        if img.imggroupID.value != self._groups[0]:
            errors.append(self._build_error(
                    img, u'il gruppo principale non è "%s"' % self._groups[0]))
            if self._stop_on_first_fail:
                return errors
        if len(img.altimg) != len(self._groups) - 1:
            errors.append(self._build_error(
                    img, 'L\'immagine non ha %d formati alternativi' % (
                            len(self._groups) - 1),))
            if self._stop_on_first_fail:
                return errors
        else:
            for i, img_group in enumerate(self._groups[1:]):
                if img.altimg[i].imggroupID.value != img_group:
                    msg = 'Il formato alternativo ' \
                        '%d non ha gruppo "%s"' % (i, img_group)
                    errors.append(self._build_error(img, msg))
                    if self._stop_on_first_fail:
                        return errors
        return errors


class ImgUsageTest(ImgTest):
    """testa gli usage delle immagini e dei formati alternativi"""
    def __init__(self, usages_list, stop_on_first_fail=False):
        """:usages: elenco degli usage di ciascun formato. Il primo elemento è
        la lista degli usage del formato principale, i seguenti delle altimg"""
        super(ImgUsageTest, self).__init__(stop_on_first_fail)
        self._usages_list = usages_list

    def _get_img_usages(self, img):
        return [ usage.value for usage in img.usage ]

    def _call_on_instance(self, img):
        errors = []
        if len(self._usages_list) != len(img.altimg) + 1:
            errors.append(self._build_error(
                img, 'L\'immagine non ha %d formati' % len(self._usages_list)))
            #if self._stop_on_first_fail:
            return errors

        for i, img in enumerate([img] + list(img.altimg)):
            if tuple(self._get_img_usages(img)) != tuple(self._usages_list[i]):
                errors.append(self._build_error(
                        img, 'L\'immagine non ha gli usage '
                        '%s' % self._usages_list[i]))
                if self._stop_on_first_fail:
                    break
        return errors


class ImgFilesTest(FilePresenceMixin, ImgTest):
     def __init__(self, mag_path, stop_on_first_fail=False):
         """:mag_path: path da cui inizia il path delle immagini
         scritto nel mag"""
         FilePresenceMixin.__init__(self, mag_path)
         ImgTest.__init__(self, stop_on_first_fail)


class ImgSizeTest(FilesizeMixin, ImgTest):
    def __init__(self, basepath, stop_on_first_fail=False):
        FilesizeMixin.__init__(self, basepath)
        ImgTest.__init__(self, stop_on_first_fail)


class ImgMd5Test(Md5Mixin, ImgTest):
    def __init__(self, basepath, stop_on_first_fail=False):
        Md5Mixin.__init__(self, basepath)
        ImgTest.__init__(self, stop_on_first_fail)


class ImgPixelSizeTest(ImgTest):
    def __init__(self, basepath, stop_on_first_fail):
        super(ImgPixelSizeTest, self).__init__(stop_on_first_fail)
        self._basepath = basepath

    def _call_on_resource(self, img):
        if not img.image_dimensions:
            return self._build_error(img, 'nessun image_dimensions')
        dim = img.image_dimensions[0]
        if not dim.imagelength.get_value():
            return self._build_error(img, 'nessun imagelength')
        if not dim.imagewidth.get_value():
            return self._build_error(img, 'nessun imagewidth')

        try:
            imagelength = int(dim.imagelength.get_value())
        except ValueError:
            return self._build_error(img, 'imagelength non numerico')
        try:
            imagewidth = int(dim.imagewidth.get_value())
        except ValueError:
            return self._build_error(img, 'imagewidth non numerico')

        if not img.file or not img.file[0].href.value:
            return self._build_error(img, 'nessun filepath')
        fpath = os.path.join(self._basepath, img.file[0].href.value)

        try:
            realsize = self._get_img_pixel_size(fpath)
        except IOError as exc:
            return self._build_error(
                img, 'impossibile calcolare dimensioni: %s' % exc)

        if realsize != (imagewidth, imagelength):
            return self._build_error(
                img, 'dimensioni in pixel non corrispondenti')

    def _get_img_pixel_size(self, imgpath):
        img = Image.open(imgpath)
        return img.size


class OcrTest(IterMagTest):
    """test su gli ocr"""
    target = 'ocr'

    def _build_error(self, mag_obj, msg):
        msg = '%s: %s' % (mag_obj.file[0].href.value, msg)
        return super(OcrTest, self)._build_error(mag_obj, msg)

    def _call_on_instance(self, ocr):
        err = self._call_on_resource(ocr)
        if err:
            return [err]
        return []


class OcrFilesTest(FilePresenceMixin, OcrTest):
    def __init__(self, basepath, stop_on_first_fail=False):
        FilePresenceMixin.__init__(self, basepath)
        OcrTest.__init__(self, stop_on_first_fail)


class OcrSizeTest(FilesizeMixin, OcrTest):
    def __init__(self, basepath, stop_on_first_fail=False):
        FilesizeMixin.__init__(self, basepath)
        OcrTest.__init__(self, stop_on_first_fail)


class OcrMd5Test(Md5Mixin, OcrTest):
    def __init__(self, basepath, stop_on_first_fail=False):
        Md5Mixin.__init__(self, basepath)
        OcrTest.__init__(self, stop_on_first_fail)


class OcrUsageTest(OcrTest):
    def __init__(self, usages, stop_on_first_fail=False):
        super(OcrUsageTest, self).__init__(stop_on_first_fail)
        self._usages = list(usages)

    def _call_on_instance(self, ocr):
        ocr_usages = [ usage.value for usage in ocr.usage ]
        if self._usages != ocr_usages:
            return [ self._build_error(
                ocr, 'non ha usage %s' % ', '.join(self._usages)) ]


class OcrFilenameTest(FilenameReMixin, OcrTest):
    def __init__(self, regex, stop_on_first_fail=False):
        FilenameReMixin.__init__(self, regex)
        OcrTest.__init__(self, stop_on_first_fail)


# class OcrSameSourceTest(OcrTest):
#     """controlla che l'ocr abbia un elemento source con stesso path
#     del suo elemento file"""
#     def __call__(self, ocr):
#         super(OcrSameSourceTest, self).__call__(ocr)
#         if not ocr.source:
#             self._fail('L\'ocr non ha elemento source')
#         src = ocr.source[0]
#         if not ocr.file or not src.href or not src.Location.value == 'URI' or\
#                 ocr.file[0].href.value != src.href.value:
#             self._fail('L\'ocr non ha source corrispondente all\'elemento file')


# class OcrNamePrefixTest(OcrTest):
#     """controlla che il nome del file  dell' ocr e del suo source abbiano
#     un prefisso stabilito"""
#     def __init__(self, prefix):
#         self._prefix = prefix

#     def __call__(self, ocr):
#         super(OcrNamePrefixTest, self).__call__(ocr)
#         fname = os.path.basename(ocr.file[0].href.value)
#         if not fname.startswith(self._prefix):
#             self._fail('Il filename dell\'ocr non inizia con %s' % self._prefix)
#         fname = os.path.basename(ocr.source[0].href.value)
#         if not fname.startswith(self._prefix):
#             self._fail('Il filename del source dell\'ocr non inizia '
#                        'con %s' % self._prefix)


# class UnifiMagLint(MagLint):
#     def __init__(self, metadigit, path, xml_file):
#         mag_name = os.path.splitext(os.path.basename(xml_file))[0]
#         self._tests = (
#             GenTest(
#                 {'stprog': u'http://www.sba.unifi.it/CMpro-v-p-210.html',
#                  'collection': u'http://www.sba.unifi.it/ImpronteDigitali',
#                  'agency': u'IT: UNFI, Università degli Studi di Firenze, '
#                  'Sistema Bibliotecario di Ateneo',
#                  'completeness': u'0', 'access_rights': u'1'}),
#             ImgGroupsTest(('tiff', 'jpeg300', 'jpeg100', 'thumbs')),
#             ImgTestGroups(('tiff', 'jpeg300', 'jpeg100', 'thumbs')),
#             ImgFileTest(path), OcrFileTest(path), ImgSizeTest(path),
#             OcrUsageTest(('3', 'b')), OcrSameSourceTest(),
#             ImgTestUsages((('1',), ('2',), ('3',), ('4', '3' , 'b'))),
#             ImgNamePrefixTest(mag_name), OcrNamePrefixTest(mag_name)
#             )
#         super(UnifiMagLint, self).__init__(metadigit)
