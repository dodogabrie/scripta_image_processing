"""
questo modulo ha il compito di trasformare un oggetto magSections.metadigit, cioè
un mag, in un documento xml in secondo lo standard METS
METS: http://www.loc.gov/standards/mets/
"""

import logging
import os

from lxml import etree

from .audio import add_audio
from .base import (
    FILE_TECH_AMDSEC_ID,
    FileGroups,
    file_element,
    fileptr_element,
    get_file_tech_amdsec,
    tech_md_wrapper,
)
from .info_extract import AgentsInfoConfigReader, MODSMappingReader
from .video import add_video
from .xmlutils import XmlUtils

log = logging.getLogger(__name__)


class MagMetsConverter:
    """
    classe astratta che legge i dati di un oggetto della maglib e li applica ad elemento
    xml, ricevuto nella forma di un Element della libreria lxml
    """

    def __init__(self, mag_object, mets_element, *args, **kwargs):
        """
        mag_object è un'elemento del mag (xmlbase.BaseXmlEntity)
        mets_element è un Element lxml dell'xml METS
        """
        self.mag_object = mag_object
        self.mets_element = mets_element

    def convert(self):
        pass  # da implementare nelle derivate

    def find_or_create_element(self, *args, **kwargs):
        return XmlUtils.find_or_create_element(*args, **kwargs)

    def get_namespace_tag(self, *args, **kwargs):
        return XmlUtils.get_namespace_tag(*args, **kwargs)

    _ns = get_namespace_tag


class MetsExporter(MagMetsConverter):
    """
    questa classe è responsabile di esportare l'intero albero di un documento MAG
    """

    def __init__(
        self, metadigit, img_change_history=False, info_parser=None, export_into=None
    ):
        """
        `metadigit`:
        `img_change_history`: if True add ChangeHistory info for derived images
        `info_parser`: ConfigParser with extra info for the export
        `export_into`: lxml <mets> element to use as starting point

        """
        self.metadigit = metadigit
        self._img_change_history = img_change_history
        self._info_parser = info_parser
        if export_into is None:
            self.mets = XmlUtils.create_element("mets")
        else:
            self.mets = export_into

    def convert(self):
        metadigit = self.metadigit
        self.mets.attrib[self._ns("schemaLocation", "xsi")] = (
            "http://www.loc.gov/METS/ http://www.loc.gov/standards/mets/mets.xsd "
            "http://www.loc.gov/mods/v3 "
            "http://www.loc.gov/standards/mods/v3/mods-3-2.xsd "
            "http://www.loc.gov/mix/ http://www.loc.gov/standards/mix/mix02/mix02.xsd "
            "http://cosimo.stanford.edu/sdr/metsrights/ "
            "https://www.loc.gov/standards/rights/METSRights.xsd "
            "http://www.loc.gov/audioMD/ "
            "https://www.loc.gov/standards/amdvmd/audioMD.xsd"
        )
        self.mets.attrib["TYPE"] = "text"

        self.find_or_create_element(
            "dmdSec", parent=self.mets, after=self._ns("metsHdr")
        )

        groups_map = {}  # associazione MAG imggroup-->METS fileGrp
        if metadigit.gen:
            gen_converter = GenConverter(metadigit.gen[0], self.mets, self._info_parser)
            gen_converter.convert()
            groups_map = gen_converter.img_group_fileGrp_map

        if metadigit.bib:
            bib = metadigit.bib[0]
            if bib.identifier and bib.identifier[0].value:
                id_ = bib.identifier[0].value
                if "_" in id_:
                    id_ = id_.split("_", 1)[1].strip()
                    id_ = "mets.bibit.{}".format(id_)
                self.mets.attrib["OBJID"] = id_

            if bib.title and bib.title[0].value:
                self.mets.attrib["LABEL"] = bib.title[0].value
            dmdSec = self.find_or_create_element(
                "dmdSec", parent=self.mets, after=self._ns("metsHdr")
            )
            dmdSec.attrib["ID"] = "dmd01"
            self._add_mods(dmdSec)

        if self._info_parser and self._info_parser.has_section("rights"):
            info = self._info_parser["rights"]
            self.mets.append(RightsBuilder().build(info))
        elif self._info_parser is None:
            self._add_default_rights()

        rights_ids = XmlUtils.xpath(self.mets, "mets:amdSec/mets:rightsMD/@ID")
        rights_id = rights_ids[0] if rights_ids else None

        StructMapBase(metadigit, self.mets, rights_id).convert()

        imgs_map = {}  # associazione seq_n -> nomenclatura img

        struct_map_root = _get_struct_div_resources_container(self.mets)

        for img_idx, img in enumerate(metadigit.img):
            ImgConverter(
                img,
                img_idx,
                self.metadigit.gen[0].img_group,
                self.mets,
                groups_map,
                imgs_map,
                struct_map_root,
            ).convert()

        self._add_ocrs(struct_map_root)
        self._add_audios(struct_map_root)
        self._add_videos(struct_map_root)

        StruLayer(
            imgs_map,
            metadigit.stru,
            self.find_or_create_element("structMap", parent=self.mets),
        ).convert()

        self._reorder()

    def _add_mods(self, dmdSec):
        bib = self.metadigit.bib[0]
        if self._info_parser and self._info_parser.has_section("mods_mapping"):
            mods_mapping = self._info_parser["mods_mapping"]
            info_reader = MODSMappingReader(mods_mapping)
            mods_info = info_reader.read(bib)
            builder = MODSBuilder()
            dmdSec.append(builder.build(mods_info))
        else:
            BibConverterMODS(bib, dmdSec).convert()

    def _add_default_rights(self):
        amdSec = etree.SubElement(self.mets, self._ns("amdSec"))
        rightsMd = etree.SubElement(amdSec, self._ns("rightsMD"))
        rightsMd.attrib["ID"] = "RIGHTS_MD_1"
        mdWrap = etree.SubElement(rightsMd, self._ns("mdWrap"))
        mdWrap.attrib["MDTYPE"] = "OTHER"
        mdWrap.attrib["OTHERMDTYPE"] = "copyrights_md"
        xmlData = etree.SubElement(mdWrap, self._ns("xmlData"))
        rightsDeclarationMd = etree.SubElement(
            xmlData, self._ns("RightsDeclarationMD", "rd")
        )
        rightsDeclarationMd.attrib["RIGHTSCATEGORY"] = "LICENSED"
        rightsDeclaration = etree.SubElement(
            rightsDeclarationMd, self._ns("RightsDeclaration", "rd")
        )
        rightsDeclaration.text = (
            "Questa risorsa digitale è liberamente accessibile per uso "
            " personale o scientifico.\nOgni uso comerciale è vietato"
        )
        rightsHolder = etree.SubElement(
            rightsDeclaration, self._ns("RightsHolder", "rd")
        )
        rightsHolderName = etree.SubElement(
            rightsHolder, self._ns("RightsHolderName", "rd")
        )
        rightsHolderName.text = "BEIC -BIBLIOTECA EUROPEA DI INFORMAZIONE E CULTURA"
        context = etree.SubElement(rightsDeclarationMd, self._ns("Context", "rd"))
        context.attrib["CONTEXTCLASS"] = "GENERAL PUBLIC"
        permissions = etree.SubElement(context, self._ns("Permissions", "rd"))
        permissions_attrs = (
            ("DISCOVER", "true"),
            ("DISPLAY", "true"),
            ("COPY", "true"),
            ("DUPLICATE", "true"),
            ("MODIFY", "false"),
            ("DELETE", "false"),
            ("PRINT", "true"),
            ("OTHER", "false"),
        )
        for k, v in permissions_attrs:
            permissions.attrib[k] = v
        context = etree.SubElement(rightsDeclarationMd, self._ns("Context", "rd"))
        context.attrib["CONTEXTCLASS"] = "REPOSITORY MGR"
        permissions = etree.SubElement(context, self._ns("Permissions", "rd"))
        permissions_attrs = (
            ("DISCOVER", "true"),
            ("DISPLAY", "true"),
            ("COPY", "true"),
            ("DUPLICATE", "true"),
            ("MODIFY", "true"),
            ("DELETE", "true"),
            ("PRINT", "true"),
            ("OTHER", "true"),
        )
        for k, v in permissions_attrs:
            permissions.attrib[k] = v

    def _add_ocrs(self, struct_map_root):
        if not self.metadigit.ocr:
            return

        file_grp = FileGroups(self.mets).create("ocr")

        for i, ocr in enumerate(self.metadigit.ocr):
            seq_n = ocr.sequence_number[0].value
            file_id = "TMD_OCR_Scan{:05d}".format(int(seq_n))
            file_el = file_element(ocr, file_id, seq_n)
            file_grp.append(file_el)

            # add the resource in the page div with the same index
            if struct_map_root is not None:
                struct_map_root[i].append(fileptr_element(file_id))

    def _add_audios(self, struct_map_root):
        if not self.metadigit.audio:
            return

        for i, audio in enumerate(self.metadigit.audio):
            file_elements = add_audio(self.mets, audio)
            if struct_map_root is not None:
                for file_el in file_elements:
                    struct_map_root[i].append(fileptr_element(file_el.attrib["ID"]))

    def _add_videos(self, struct_map_root):
        if not self.metadigit.video:
            return

        for i, video in enumerate(self.metadigit.video):
            file_elements = add_video(self.mets, video)
            if struct_map_root is not None:
                for file_el in file_elements:
                    struct_map_root[i].append(fileptr_element(file_el.attrib["ID"]))

    def _reorder(self):
        for amdSec in [child for child in self.mets if child.tag == self._ns("amdSec")]:
            if amdSec.attrib.get("ID") == FILE_TECH_AMDSEC_ID:
                self.mets.append(amdSec)

        for amdSec in [child for child in self.mets if child.tag == self._ns("amdSec")]:
            if amdSec[0].tag == self._ns("rightsMD"):
                self.mets.append(amdSec)

        for child in self.mets:
            if child.tag == self._ns("fileSec"):
                self.mets.append(child)

        for child in self.mets:
            if child.tag == self._ns("structMap"):
                self.mets.append(child)


class StructMapBase:
    """Build the basic nodes of structMap representing resource nomenclatures

    A structure with 2 levels is built when the mag has multiple resources:
    - structMap -> div -> div (a div for every resource)

    A structure with one level is built when the mag has only one resource
    * structMap -> div (div for the only resource)

    """

    def __init__(self, metadigit, mets_el, root_div_adm):
        self._metadigit = metadigit
        self._mets_el = mets_el
        self._root_div_admid = root_div_adm

    def convert(self):
        struct_map = XmlUtils.find_or_create_element("structMap", parent=self._mets_el)

        main_resource_type = self._get_main_resource_type()

        if not main_resource_type:
            log.warning("No resources found")
            return

        nomenclatures = self._get_nomenclatures(main_resource_type)

        assert len(nomenclatures) > 0
        if len(nomenclatures) > 1 or main_resource_type == "img":
            root_div = etree.SubElement(struct_map, XmlUtils.ns("div"))
            root_label = self._get_root_label()
            if root_label:
                root_div.attrib["LABEL"] = root_label
            if main_resource_type == "img":
                root_div.attrib["TYPE"] = "book"

            for nom in nomenclatures:
                div = etree.SubElement(root_div, XmlUtils.ns("div"))
                if main_resource_type not in ("audio", "video"):
                    div.attrib["TYPE"] = "page"
                div.attrib["LABEL"] = nom
        else:
            div = etree.SubElement(struct_map, XmlUtils.ns("div"))
            if main_resource_type in ("audio", "video"):
                div.attrib["TYPE"] = main_resource_type
            if nomenclatures[0]:
                div.attrib["LABEL"] = nomenclatures[0]

        root_div = struct_map[0]
        # la root punta ai metadati descrittivi generali
        root_div.attrib["DMDID"] = "dmd01"
        if self._root_div_admid:
            root_div.attrib["ADMID"] = self._root_div_admid

    def _get_main_resource_type(self):
        # The main resource type of the mag
        # resource_type with nomenclatures is preferred
        # fallback to any resource type found
        for resource_type in ("img", "audio", "video", "ocr", "doc"):
            rsrcs_node = getattr(self._metadigit, resource_type)
            if rsrcs_node:
                first_rsrc = rsrcs_node[0]
                if first_rsrc.nomenclature and first_rsrc.nomenclature[0].value:
                    return resource_type

        for resource_type in ("img", "audio", "video", "ocr", "doc"):
            rsrcs_node = getattr(self._metadigit, resource_type)
            if rsrcs_node:
                return resource_type

        return None

    def _get_nomenclatures(self, main_rsrc_type):
        rsrcs_node = getattr(self._metadigit, main_rsrc_type)
        return [r.nomenclature[0].value if r.nomenclature else "" for r in rsrcs_node]

    def _get_root_label(self):
        if (
            self._metadigit.bib
            and self._metadigit.bib[0].title
            and self._metadigit.bib[0].title[0].value
        ):
            return self._metadigit.bib[0].title[0].value
        else:
            return None


class ImgConverter(MagMetsConverter):
    """
    classe responsabile di inserire i dati di una singola immagine del mag
    nel documento mets
    """

    def __init__(
        self,
        img,
        img_idx,
        img_group,
        mets_element,
        groups_map,
        img_seq_map,
        struct_map_root,
        img_change_history=False,
    ):
        self.img = img
        self._img_idx = img_idx
        self.img_group = img_group
        self.mets_element = mets_element
        # lista con gli id delle sezioni techMd create,
        # in ordine a partire dal formato master
        self.techMd_id = []
        self.groups_map = groups_map
        # dizionario con chiave numero sequenza immagine, valore nomenclatura immagine
        self.img_seq_map = img_seq_map
        self._struct_map_root = struct_map_root
        self._img_change_history = img_change_history

    def convert(self):
        img_seq_n = self.img.sequence_number[0].value
        img_id = "TMD_MASTER_IMG_Scan%05u" % int(img_seq_n)
        techMd_id = "{}_techMD".format(img_id)

        self.techMd_id.append(techMd_id)

        amdSec = get_file_tech_amdsec(self.mets_element)
        techMd = self._build_techMd(self.img, techMd_id, master_img=True)
        amdSec.append(techMd)

        # aggiungo un elemento file per l'immagine, per sapere in che fileGrp
        #  và ho bisogno dell'imggroup
        # imggroup_id = self._find_img_group_by_id(self.img.imggroupID.value)

        group_id = self.groups_map[self.img.imggroupID.value]
        fileGrp = FileGroups(self.mets_element).find(group_id)
        img_seq_n = self.img.sequence_number[0].value
        fiLe = file_element(self.img, img_id, img_seq_n, techMd_id)

        fileGrp.append(fiLe)
        # mappa numero di sequenza-id nel mets dell'immagine
        self.img_seq_map[
            int(self.img.sequence_number[0].value)
        ] = self.img.nomenclature[0].value

        page_div = self._struct_map_root[self._img_idx]

        page_div.append(fileptr_element(fiLe.attrib["ID"]))

        for altimg_idx, altimg in enumerate(self.img.altimg, 1):
            altimg_id = "TMD_DRV%u_IMG_Scan%05u" % (altimg_idx, int(img_seq_n))
            techMd_id = "{}_techMD".format(altimg_id)
            techMd = self._build_techMd(altimg, techMd_id, master_img=False)

            amdSec.append(techMd)
            fiLe = file_element(altimg, altimg_id, img_seq_n, techMd_id)
            group_id = self.groups_map[altimg.imggroupID.value]
            fileGrp = FileGroups(self.mets_element).find(group_id)
            fileGrp.append(fiLe)

            page_div.append(fileptr_element(fiLe.attrib["ID"]))

    def _find_img_group_by_id(self, img_group_id):
        for img_group in self.img_group:
            if img_group.ID.value == img_group_id:
                return img_group
        return None

    def _build_techMd(self, img, tech_md_id, master_img):
        # master img distingue se si tratta del techMD del formato master o meno
        techMd = tech_md_wrapper(tech_md_id, "NISOIMG")
        xmlData = techMd[0][0]
        mix = etree.SubElement(xmlData, self._ns("mix", "mix"))

        img_group = self._find_img_group_by_id(img.imggroupID.value)
        if img_group and img_group.format:
            ImgFormatConverter02(img_group.format[0], mix).convert()

        if master_img and img_group and img_group.scanning:
            ImgScanningConverter02(
                img.datetimecreated[0].value, img_group.scanning[0], mix
            ).convert()

        if img_group and img_group.image_metrics:
            ImgMetricsConverter02(img_group.image_metrics[0], mix).convert()

        basic_img_params = self.find_or_create_element(
            "BasicImageParameters", namespace="mix", parent=mix
        )
        fiLe = self.find_or_create_element(
            "File",
            namespace="mix",
            parent=basic_img_params,
            after=self._ns("Format", "mix"),
        )
        orientation = self.find_or_create_element(
            "Orientation", namespace="mix", parent=fiLe
        )
        orientation.text = "1"
        display_orientation = self.find_or_create_element(
            "DisplayOrientation",
            namespace="mix",
            parent=fiLe,
            after=self._ns("Orientation", "mix"),
        )
        display_orientation.text = "0"

        if img.format:
            ImgFormatConverter02(img.format[0], mix).convert()
        # la sezione scanning è solo per il formato principale
        if master_img and img.scanning:
            ImgScanningConverter02(
                img.datetimecreated[0].value, img.scanning, mix
            ).convert()
        if img.image_metrics:
            ImgMetricsConverter02(img.image_metrics[0], mix).convert()

        if img.image_dimensions:
            if (
                img.image_dimensions[0].imagelength
                and img.image_dimensions[0].imagewidth
            ):
                self._add_img_dimensions_02(mix, img.image_dimensions[0])
            #            if img.image_dimensions[0].source_xdimension and\
            #                    img.image_dimensions[0].source_ydimension:
            # aggiungo le dimensioni dell'immagine fisica solo per il formato master
            # le calcolo a partire dai dpi
            if master_img:
                dpi = 400
                src_dimensions = (
                    float(img.image_dimensions[0].imagewidth[0].value) / dpi,
                    float(img.image_dimensions[0].imagelength[0].value) / dpi,
                )
                self._add_src_dimensions(mix, src_dimensions)

        if img.filesize and img.filesize[0].value:
            self._add_filesize_02(mix, img.filesize[0].value)

        if img.md5 and img.md5[0].value:
            self._add_md5_02(mix, img.md5[0].value)

        for child in mix:
            if child.tag == self._ns("ImagingPerformanceAssessment", "mix"):
                mix.append(child)

        if not master_img and self._img_change_history:
            change_history = etree.SubElement(mix, self._ns("ChangeHistory", "mix"))
            image_processing = etree.SubElement(
                change_history, self._ns("ImageProcessing", "mix")
            )
            datetime_processed = etree.SubElement(
                image_processing, self._ns("DateTimeProcessed", "mix")
            )
            datetime_processed.text = img.datetimecreated[0].value
            software = etree.SubElement(
                image_processing, self._ns("ProcessingSoftware", "mix")
            )
            software_name = etree.SubElement(
                software, self._ns("ProcessingSoftwareName", "mix")
            )
            software_name.text = "Python Imaging Library"
            # software_version = etree.SubElement(
            # software, self._ns("ProcessingSoftwareVersion", "mix")
            # )
            # software_version = "1.1.6"

            img_group = self._find_img_group_by_id(img.imggroupID.value)
            dpi = img_group.image_metrics[0].xsamplingfrequency

            first_actions = etree.SubElement(
                image_processing, self._ns("ProcessingActions", "mix")
            )
            first_actions.text = "Resize to %s dot-per-inch" % dpi

            actions = etree.SubElement(
                image_processing, self._ns("ProcessingActions", "mix")
            )
            actions.text = "Conversion from Tiff to Jpeg format"

        #        if img.datetimecreated and img.datetimecreated[0].value:
        #            self._add_scanning_date(mix, img.datetimecreated[0].value)

        return techMd

    def _add_filesize_02(self, mix_element, filesize):
        basic_img_params = self.find_or_create_element(
            "BasicImageParameters", namespace="mix", parent=mix_element
        )
        file = self.find_or_create_element(
            "File",
            namespace="mix",
            parent=basic_img_params,
            after=self._ns("Format", "mix"),
        )
        file_size = self.find_or_create_element(
            "FileSize", namespace="mix", parent=file
        )
        file_size.text = filesize

    def _add_md5_02(self, mix_element, md5):
        basic_img_params = self.find_or_create_element(
            "BasicImageParameters", namespace="mix", parent=mix_element
        )
        file = self.find_or_create_element(
            "File",
            namespace="mix",
            parent=basic_img_params,
            after=self._ns("Format", "mix"),
        )
        checksum = self.find_or_create_element(
            "Checksum", namespace="mix", parent=file, after=self._ns("FileSize", "mix")
        )
        checksum_method = self.find_or_create_element(
            "ChecksumMethod", namespace="mix", parent=checksum
        )
        checksum_method.text = "MD5"
        checksum_value = self.find_or_create_element(
            "ChecksumValue",
            namespace="mix",
            parent=checksum,
            after=self._ns("ChecksumMethod", "mix"),
        )
        checksum_value.text = md5

    def _add_img_dimensions_02(self, mix_element, img_dimensions):
        # aggiunge le dimensioni dell'immagine all'elemento mets
        img_ass = self.find_or_create_element(
            "ImagingPerformanceAssessment",
            namespace="mix",
            parent=mix_element,
            after=self._ns("ImageCreation", namespace="mix"),
        )

        spatialMetrics = self.find_or_create_element(
            "SpatialMetrics", namespace="mix", parent=img_ass
        )

        if img_dimensions.imagewidth and img_dimensions.imagewidth[0].value:
            imageWidth = self.find_or_create_element(
                "ImageWidth",
                namespace="mix",
                parent=spatialMetrics,
                after=self._ns("YSamplingFrequency", "mix"),
            )
            imageWidth.text = img_dimensions.imagewidth[0].value
            # imageWidth.text = img_dimensions.imagelength[0].value

        if img_dimensions.imagelength and img_dimensions.imagelength[0].value:
            imageHeight = self.find_or_create_element(
                "ImageLength",
                namespace="mix",
                parent=spatialMetrics,
                after=self._ns("ImageWidth", "mix"),
            )
            imageHeight.text = img_dimensions.imagelength[0].value

    def _add_src_dimensions(self, mix_element, src_dimensions):
        img_ass = self.find_or_create_element(
            "ImagingPerformanceAssessment",
            namespace="mix",
            parent=mix_element,
            after=self._ns("ImageCreation", namespace="mix"),
        )

        spatialMetrics = self.find_or_create_element(
            "SpatialMetrics", namespace="mix", parent=img_ass
        )

        x_dim = self.find_or_create_element(
            "Source_X",
            namespace="mix",
            parent=spatialMetrics,
            after=self._ns("ImageLength", "mix"),
        )
        x_dim_unit = self.find_or_create_element(
            "Source_XdimensionUnit", namespace="mix", parent=x_dim
        )
        x_dim_unit.text = "in."
        x_dim_value = self.find_or_create_element(
            "Source_Xdimension", namespace="mix", parent=x_dim
        )
        # x_dim_value.text = str(src_dimensions[0])
        x_dim_value.text = str(src_dimensions[1])

        y_dim = self.find_or_create_element(
            "Source_Y",
            namespace="mix",
            parent=spatialMetrics,
            after=self._ns("Source_X", "mix"),
        )
        y_dim_unit = self.find_or_create_element(
            "Source_YdimensionUnit", namespace="mix", parent=y_dim
        )
        y_dim_unit.text = "in."
        y_dim_value = self.find_or_create_element(
            "Source_Ydimension", namespace="mix", parent=y_dim
        )
        # y_dim_value.text = str(src_dimensions[1])
        y_dim_value.text = str(src_dimensions[0])

    def _add_scanning_date(
        self, mix_element, date_value
    ):  # aggiunge la data in cui si è effettuata la scansione
        img_capture = self.find_or_create_element(
            "ImageCaptureMetadata",
            namespace="mix",
            parent=mix_element,
            after=self._ns("BasicImageInformation", "mix"),
        )
        gen_capture_info = self.find_or_create_element(
            "GeneralCaptureInformation",
            namespace="mix",
            parent=img_capture,
            after=self._ns("SourceInformation", "mix"),
        )
        date = self.find_or_create_element(
            "dateTimeCreated", namespace="mix", parent=gen_capture_info
        )
        date.text = date_value

    def _get_file_id(self, img):
        img_path = img.file[0].href.value
        img_basename = os.path.basename(img_path)
        return os.path.splitext(img_basename)[0]

    def _get_master_techMd_id(self):
        # ottengo l'id a partire dal nome del file
        return self._get_file_id(self.img) + "_techMD"

    def _get_altimg_techMd_id(self, altimg):
        # ottengo l'id a partire dal nome del file e dall'id del groppo
        # return '%s_%s_techMD' % (self._get_file_id(self.img), imggroup_id)
        return self._get_file_id(altimg) + "_techMD"


class BibConverter(MagMetsConverter):
    """
    questa classe importa la sezione bib del mag nel documento mets
    """

    def __init__(self, *args, **kwargs):
        super(BibConverter, self).__init__(*args, **kwargs)
        self.bib = self.mag_object
        self.dmdSec = self.mets_element

    def convert(self):
        mdWrap = self.find_or_create_element("mdWrap", parent=self.dmdSec)
        mdWrap.attrib["MDTYPE"] = "DC"
        mdWrap.attrib["LABEL"] = "Metadati descrittivi"
        xmlData = self.find_or_create_element("xmlData", parent=mdWrap)

        for dc_field in (
            "identifier",
            "title",
            "creator",
            "publisher",
            "subject",
            "description",
            "contributor",
            "date",
            "type",
            "format",
            "source",
            "language",
            "relation",
            "coverage",
            "rights",
        ):
            for dc_element in getattr(self.bib, dc_field):
                if dc_element.Visible:
                    el_string = dc_element.AsTag().toxml()
                    el_string = el_string.replace("dc:", "")
                    el = etree.fromstring(el_string)
                    el.tag = XmlUtils.get_namespace_tag(el.tag, "dc")
                    xmlData.append(el)


class BibConverterMODS(MagMetsConverter):
    """importa la sezione bib del mag nel documento mets in formato MODS"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bib = self.mag_object
        self.dmdSec = self.mets_element

    def convert(self):
        mdWrap = self.find_or_create_element("mdWrap", parent=self.dmdSec)
        mdWrap.attrib["MDTYPE"] = "MODS"
        xmlData = self.find_or_create_element("xmlData", parent=mdWrap)
        mods = self.find_or_create_element("mods", namespace="mods", parent=xmlData)

        if self.bib.title and self.bib.title[0].value:
            titleInfo = self.find_or_create_element(
                "titleInfo", namespace="mods", parent=mods
            )
            title = self.find_or_create_element(
                "title", namespace="mods", parent=titleInfo
            )
            title.text = self.bib.title[0].value

        def _name():
            return self.find_or_create_element(
                "name",
                namespace="mods",
                after=self._ns("titleInfo", "mods"),
                parent=mods,
            )

        def _originInfo():
            return self.find_or_create_element(
                "originInfo",
                namespace="mods",
                after=self._ns("typeOfResource", "mods"),
                parent=mods,
            )

        if self.bib.creator and self.bib.creator[0].value:
            name = _name()
            namePart = self.find_or_create_element(
                "namePart", namespace="mods", parent=name
            )
            namePart.text = self.bib.creator[0].value

        if self.bib.publisher and self.bib.publisher[0].value:
            name = _name()
            role = self.find_or_create_element(
                "role",
                namespace="mods",
                after=self._ns("namePart", "mods"),
                parent=name,
            )
            roleTerm = self.find_or_create_element(
                "roleTerm", namespace="mods", parent=role
            )
            roleTerm.attrib["type"] = "text"
            roleTerm.text = "Autore"
            # typeOfResource = self.find_or_create_element(
            #     "typeOfResource",
            #     namespace="mods",
            #     after=self._ns("name", "mods"),
            #     parent=mods,
            # )
            # typeOfResource.text = "still image"
            originInfo = _originInfo()
            place = self.find_or_create_element(
                "place", namespace="mods", parent=originInfo
            )
            placeTerm = self.find_or_create_element(
                "placeTerm", namespace="mods", parent=place
            )
            placeTerm.attrib["type"] = "text"
            sq = self.bib.publisher[0].value.lstrip().startswith("[")
            place_string = (
                self.bib.publisher[0]
                .value.lstrip()
                .replace("[", "")
                .replace("]", "")
                .split(":")[0]
                .strip()
            )
            if sq:
                place_string = "[%s]" % place_string
            placeTerm.text = place_string

            publisher = self.find_or_create_element(
                "publisher",
                namespace="mods",
                after=self._ns("place", "mods"),
                parent=originInfo,
            )
            sq = self.bib.publisher[0].value.rstrip().endswith("]")

            pub_string = (
                self.bib.publisher[0]
                .value.strip()
                .replace("[", "")
                .replace("]", "")
                .strip()
            )
            if ":" in pub_string:
                pub_string = pub_string.split(":")[1]

            if sq:
                pub_string = "[%s]" % pub_string
            publisher.text = pub_string

        if self.bib.date and self.bib.date[0].value:
            originInfo = _originInfo()
            date = self.find_or_create_element(
                "dateIssued",
                namespace="mods",
                after=self._ns("publisher", "mods"),
                parent=originInfo,
            )
            date.text = self.bib.date[0].value

        # language = self.find_or_create_element('language', namespace='mods', after=self._ns('originInfo', 'mods'), parent=mods)
        # languageTerm = self.find_or_create_element('languageTerm', namespace='mods', parent=language)
        # languageTerm.attrib['authority'] = 'iso639-2b'
        # languageTerm.attrib['type'] = 'code'
        # languageTerm.text = 'it'

        # id1 = self.find_or_create_element('identifier', namespace='mods', after=self._ns('originInfo', 'mods'), parent=mods)
        # id1.text = self.bib.identifier[0].value.split('_')[1].strip()#[3:].strip()
        # id1.attrib['type'] = 'IGI'
        if self.bib.identifier and self.bib.identifier[0].value:
            id2 = etree.SubElement(mods, self._ns("identifier", "mods"))
            id2.text = self.bib.identifier[0].value
            id2.attrib["type"] = "ISTC"


class GenConverter(MagMetsConverter):
    """
    questa classe importa nel documento mets la sezione gen del mag
    """

    def __init__(self, gen, mets_element, info_parser):
        super().__init__(gen, mets_element)
        self.gen = self.mag_object
        self.img_group_fileGrp_map = {}
        self._info_parser = info_parser

    def convert(self):
        if self._info_parser is None:
            agents_info = self._default_agents_info()
        else:
            reader = AgentsInfoConfigReader()
            agents_info = reader.read(self._info_parser)

        metsHdr = self.find_or_create_element("metsHdr", parent=self.mets_element)
        mets_builder = MetsHdrBuilder()
        mets_builder.build(self.gen, agents_info, metsHdr)

        # amdSec = self.find_or_create_element(
        #    'amdSec', parent=self.mets_element, after=self._ns('metsHdr') )

        # aggiungo gli img_group
        # il num sequenziale di img group è utile per calcolare alcuni campi del techMD
        img_group_seq_number = 1
        for img_group in self.gen.img_group:
            # techMd = etree.SubElement(amdSec, self._ns('techMD'))
            # label = self.get_tech_md_label(img_group_seq_number)
            # creo il techMd per il gruppo
            # ImgGroupTechConverter(img_group, techMd, id, label).convert()

            # ad ogni img_group corrisponde però anche un fileGrp
            group_id = self.convert_img_group_id(
                img_group.ID.value, img_group_seq_number, prefix="fileGroup"
            )
            fileGrp = FileGroups(self.mets_element).find_or_create(group_id)
            fileGrp.attrib["USE"] = self.get_usage(img_group_seq_number)

            #     # devo tenere mappato l'id dell'img_group con l'id del fileGrp
            self.img_group_fileGrp_map[img_group.ID.value] = fileGrp.attrib["ID"]

            img_group_seq_number += 1

    def _default_agents_info(self):
        """The default agents info when not passed via info parser"""

        agents_info = [
            {"role": "CREATOR", "type": "ORGANIZATION", "name": "Space S.p.a."}
        ]

        # l'agent che si riferisce al gestore del documento fisico
        if self.gen.agency and self.gen.agency[0].value:
            data_agent = {
                "role": "ARCHIVIST",
                "type": "ORGANIZATION",
                "name": self.gen.agency[0].value,
            }
            agents_info.append(data_agent)

        return agents_info

    def get_usage(self, img_group_seq_number):
        # ritorna l'usage dell'img group
        usage_dict = {
            1: "master",
            2: "alta risoluzione",
            3: "bassa risoluzione",
            4: "preview",
        }
        try:
            return usage_dict[img_group_seq_number]
        except KeyError:
            return None

    def get_tech_md_label(self, img_group_seq_number):
        # ritorna la label del mdWrap contenuto in un techMD

        # ritorno 'Metadati tecnici immagini master' per il primo techMd (imgGroup),
        # 'Metadati tecnici immagini alta risoluzione' per il secondo techMd,
        # 'Metadati tecnici immagini bassa risoluzione'
        labels_dict = {
            1: "Metadati tecnici immagini master",
            2: "Metadati tecnici immagini alta risoluzione",  # controllare
            3: "Metadati tecnici immagini bassa risoluzione",
        }
        try:
            return labels_dict[img_group_seq_number]
        except KeyError:
            return None

    def convert_img_group_id(
        self, img_group_id, img_group_seq_number, prefix="gen_techMD"
    ):
        # metodo per ottenere gli id di una sezione techMD a
        # partire dall'ID del imgGroup del MAG
        # questo creatore di id ritorna id nella forma $prefisso$numero_sequenziale,
        tech_md_id = "%s%02u" % (prefix, img_group_seq_number)
        return tech_md_id


class ImgGroupTechConverter(MagMetsConverter):
    """
    questa classe esporta un imggroup in un techMD
    """

    def __init__(self, img_group, techMd_element, id=None, label=None, *args, **kwargs):
        # id e label vengono calcolati a livello superiore e passati quà
        super(ImgGroupTechConverter, self).__init__(
            img_group, techMd_element, *args, **kwargs
        )
        self.img_group = self.mag_object
        self.techMd = self.mets_element
        self.techMd_label = label
        self.techMd_id = id

    def convert(self):
        if self.techMd_id:
            self.techMd.attrib["ID"] = self.techMd_id

        mdWrap = self.find_or_create_element("mdWrap", parent=self.techMd)

        if self.techMd_label:
            mdWrap.attrib["LABEL"] = self.techMd_label

        mdWrap.attrib["MDTYPE"] = "NISOIMG"
        mdWrap.attrib["MIMETYPE"] = "text/xml"

        xmlData = self.find_or_create_element("xmlData", parent=mdWrap)
        mix = self.find_or_create_element("mix", namespace="mix", parent=xmlData)

        if self.img_group.format:
            ImgFormatConverter02(self.img_group.format[0], mix).convert()

        if self.img_group.scanning:
            ImgScanningConverter02(self.img_group.scanning[0], mix).convert()

        if self.img_group.image_metrics:
            ImgMetricsConverter02(self.img_group.image_metrics[0], mix).convert()

        # aggiungo arbitrariamente "l'orientamento" della pagina
        basic_img_params = self.find_or_create_element(
            "BasicImageParameters", namespace="mix", parent=mix
        )
        fiLe = self.find_or_create_element(
            "File",
            namespace="mix",
            parent=basic_img_params,
            after=self._ns("Format", "mix"),
        )
        orientation = self.find_or_create_element(
            "Orientation",
            namespace="mix",
            parent=fiLe,
            after=self._ns("Checksum", "mix"),
        )
        orientation.text = "1"
        display_orientation = self.find_or_create_element(
            "DisplayOrientation",
            namespace="mix",
            parent=fiLe,
            after=self._ns("Orientation", "mix"),
        )
        display_orientation.text = "0"
        ###


class ImgFormatConverter(MagMetsConverter):
    """
    inserisce i dati dell'elemento format (che si può trovare in una  img o in
    un img_group ) in un elemento xml in formato MIX
    """

    def __init__(self, *args, **kwargs):
        super(ImgFormatConverter, self).__init__(*args, **kwargs)
        self.img_format = self.mag_object
        self.mix = self.mets_element

    def convert(self):
        basic_do_info = self.find_or_create_element(
            "BasicDigitalObjectInformation", namespace="mix", parent=self.mix
        )

        # provo ad aggiungere il mimetype
        if self.img_format.mime and self.img_format.mime[0].value:
            format_designation = self.find_or_create_element(
                "FormatDesignation", namespace="mix", parent=basic_do_info
            )
            format_name = self.find_or_create_element(
                "formatName", namespace="mix", parent=format_designation
            )
            format_name.text = self.img_format.mime[0].value

        # aggiungo l'"endianess", quì anche se non è (tutto little-endian??)
        byteOrder = self.find_or_create_element(
            "byteOrder", namespace="mix", parent=basic_do_info
        )
        byteOrder.text = "little endian"

        # aggiungo la compressione
        # (la aggiungo anche se non la trovo nel mag, il default è "Uncompressed")
        compression = self.find_or_create_element(
            "Compression", namespace="mix", parent=basic_do_info
        )
        if self.img_format.compression and self.img_format.compression[0].value:
            mag_compression = self.img_format.compression[0].value
        else:
            mag_compression = "Uncompressed"
        compression_scheme = self.find_or_create_element(
            "compressionScheme", namespace="mix", parent=compression
        )
        compression_scheme.text = mag_compression


class ImgFormatConverter02(MagMetsConverter):
    """
    inserisce i dati dell'elemento format (che si può trovare in una  img o in
    un img_group ) in un elemento xml in formato MIX 02
    """

    COMPRESSION_MAP = {"Uncompressed": "1", "JPEG": "6", "JPG": "6"}

    def __init__(self, *args, **kwargs):
        super(ImgFormatConverter02, self).__init__(*args, **kwargs)
        self.img_format = self.mag_object
        self.mix = self.mets_element

    def convert(self):
        basic_img_params = self.find_or_create_element(
            "BasicImageParameters", namespace="mix", parent=self.mix
        )
        format = self.find_or_create_element(
            "Format", namespace="mix", parent=basic_img_params
        )

        # provo ad aggiungere il mimetype
        if self.img_format.mime and self.img_format.mime[0].value:
            mimetype = self.find_or_create_element(
                "MIMEType", namespace="mix", parent=format
            )
            mimetype.text = self.img_format.mime[0].value

        # aggiungo l'"endianess", quì anche se non è (tutto little-endian??)
        byteOrder = self.find_or_create_element(
            "ByteOrder",
            namespace="mix",
            parent=format,
            after=self._ns("MIMEType", "mix"),
        )
        byteOrder.text = "little-endian"

        # aggiungo la compressione
        # (la aggiungo anche se non la trovo nel mag, il default è "Uncompressed")
        compression = self.find_or_create_element(
            "Compression",
            namespace="mix",
            parent=format,
            after=self._ns("ByteOrder", "mix"),
        )
        if self.img_format.compression and self.img_format.compression[0].value:
            mag_compression = self.img_format.compression[0].value
        else:
            mag_compression = "Uncompressed"
        compression_scheme = self.find_or_create_element(
            "CompressionScheme", namespace="mix", parent=compression
        )
        compression_scheme.text = self.COMPRESSION_MAP[mag_compression]


class ImgMetricsConverter02(MagMetsConverter):
    COLORSPACE_MAP = {"RGB": "2"}

    def __init__(self, *args, **kwargs):
        super(ImgMetricsConverter02, self).__init__(*args, **kwargs)
        self.img_metrics = self.mag_object
        self.mix = self.mets_element

    def convert(self):
        basic_img_params = self.find_or_create_element(
            "BasicImageParameters", namespace="mix", parent=self.mix
        )
        format = self.find_or_create_element(
            "Format", namespace="mix", parent=basic_img_params
        )
        img_ass = self.find_or_create_element(
            "ImagingPerformanceAssessment",
            namespace="mix",
            parent=self.mix,
            after=self._ns("ImageCreation", namespace="mix"),
        )

        spatialMetrics = self.find_or_create_element(
            "SpatialMetrics", namespace="mix", parent=img_ass
        )

        if (
            self.img_metrics.samplingfrequencyunit
            and self.img_metrics.samplingfrequencyunit[0].value
        ):
            samplingFrequencyUnit = self.find_or_create_element(
                "SamplingFrequencyUnit",
                namespace="mix",
                parent=spatialMetrics,
                after=self._ns("SamplingFrequencyPlane", "mix"),
            )
            samplingFrequencyUnit.text = self.img_metrics.samplingfrequencyunit[0].value

        if (
            self.img_metrics.xsamplingfrequency
            and self.img_metrics.xsamplingfrequency[0].value
        ):
            xsamplingFrequency = self.find_or_create_element(
                "XSamplingFrequency",
                namespace="mix",
                parent=spatialMetrics,
                after=self._ns("SamplingFrequencyUnit", "mix"),
            )
            xsamplingFrequency.text = self.img_metrics.xsamplingfrequency[0].value

        if (
            self.img_metrics.ysamplingfrequency
            and self.img_metrics.ysamplingfrequency[0].value
        ):
            ysamplingFrequency = self.find_or_create_element(
                "YSamplingFrequency",
                namespace="mix",
                parent=spatialMetrics,
                after=self._ns("XSamplingFrequency", "mix"),
            )
            ysamplingFrequency.text = self.img_metrics.ysamplingfrequency[0].value

        if (
            self.img_metrics.photometricinterpretation
            and self.img_metrics.photometricinterpretation[0].value
        ):
            ph_m_i = self.find_or_create_element(
                "PhotometricInterpretation",
                namespace="mix",
                parent=format,
                after=self._ns("Compression", "mix"),
            )
            colorspace = self.find_or_create_element(
                "ColorSpace", namespace="mix", parent=ph_m_i
            )
            colorspace.text = self.COLORSPACE_MAP[
                self.img_metrics.photometricinterpretation[0].value
            ]
            reference_bw = self.find_or_create_element(
                "ReferenceBlackWhite",
                namespace="mix",
                parent=ph_m_i,
                after=self._ns("ColorSpace", "mix"),
            )
            reference_bw.text = "0.0 255.0 0.0 255.0 0.0 255.0"

        if self.img_metrics.bitpersample and self.img_metrics.bitpersample[0].value:
            img_energetics = self.find_or_create_element(
                "Energetics",
                namespace="mix",
                parent=img_ass,
                after=self._ns("SpatialMetrics", "mix"),
            )
            bitspersample = self.find_or_create_element(
                "BitsPerSample", namespace="mix", parent=img_energetics
            )
            bitspersample.text = self.img_metrics.bitpersample[0].value
            samplesperpixel = self.find_or_create_element(
                "SamplesPerPixel",
                namespace="mix",
                parent=img_energetics,
                after=self._ns("BitsPerSample", "mix"),
            )
            samplesperpixel.text = str(len(bitspersample.text.split(",")))


class ImgScanningConverter(MagMetsConverter):
    def __init__(self, *args, **kwargs):
        super(ImgScanningConverter, self).__init__(*args, **kwargs)
        self.img_scanning = self.mag_object
        self.mix = self.mets_element

    def convert(self):
        img_capture = self.find_or_create_element(
            "ImageCaptureMetadata",
            namespace="mix",
            parent=self.mix,
            after=self._ns("BasicImageInformation", "mix"),
        )

        if self.img_scanning.sourcetype and self.img_scanning.sourcetype[0].value:
            src_information = self.find_or_create_element(
                "SourceInformation", namespace="mix", parent=img_capture
            )
            src_type = self.find_or_create_element(
                "sourceType", namespace="mix", parent=src_information
            )
            src_type.text = self.img_scanning.sourcetype[0].value

        general_capture_info = self.find_or_create_element(
            "GeneralCaptureInformation", namespace="mix", parent=img_capture
        )
        if (
            self.img_scanning.scanningagency
            and self.img_scanning.scanningagency[0].value
        ):
            img_producer = self.find_or_create_element(
                "imageProducer", namespace="mix", parent=general_capture_info
            )
            img_producer.text = self.img_scanning.scanningagency[0].value

        if self.img_scanning.devicesource and self.img_scanning.devicesource[0].value:
            captureDevice = self.find_or_create_element(
                "captureDevice", namespace="mix", parent=general_capture_info
            )
            captureDevice.text = self.img_scanning.devicesource[0].value

        scanner_capture = self.find_or_create_element(
            "ScannerCapture", namespace="mix", parent=img_capture
        )
        if self.img_scanning.scanningsystem:
            s_system = self.img_scanning.scanningsystem[0]
            if s_system.scanner_manufacturer and s_system.scanner_manufacturer[0].value:
                scannerManufacturer = self.find_or_create_element(
                    "scannerManufacturer", namespace="mix", parent=scanner_capture
                )
                scannerManufacturer.text = s_system.scanner_manufacturer[0].value
            if s_system.scanner_model and s_system.scanner_model[0].value:
                scannerModel = self.find_or_create_element(
                    "scannerModel", namespace="mix", parent=scanner_capture
                )
                scannerModelName = self.find_or_create_element(
                    "scannerModelName", namespace="mix", parent=scannerModel
                )
                scannerModelName.text = s_system.scanner_model[0].value

            if s_system.capture_software and s_system.capture_software[0].value:
                scanningSystemSoftware = self.find_or_create_element(
                    "scanningSystemSoftware", namespace="mix", parent=scanner_capture
                )
                scanningSystemSoftwareName = self.find_or_create_element(
                    "scanningSystemSoftwareName",
                    namespace="mix",
                    parent=scanningSystemSoftware,
                )
                scanningSystemSoftwareName.text = s_system.capture_software[0].value


class ImgScanningConverter02(MagMetsConverter):
    def __init__(self, creation_time, *args, **kwargs):
        super(ImgScanningConverter02, self).__init__(*args, **kwargs)
        self.creation_time = creation_time
        self.img_scanning = self.mag_object
        self.mix = self.mets_element

    def convert(self):
        img_capture = self.find_or_create_element(
            "ImageCreation",
            namespace="mix",
            parent=self.mix,
            after=self._ns("BasicImageParameters", "mix"),
        )

        if (
            self.img_scanning.scanningagency
            and self.img_scanning.scanningagency[0].value
        ):
            img_producer = self.find_or_create_element(
                "ImageProducer", namespace="mix", parent=img_capture
            )
            img_producer.text = self.img_scanning.scanningagency[0].value

        device_source = self.find_or_create_element(
            "DeviceSource", namespace="mix", parent=img_capture
        )
        device_source.text = "scanner"

        scan_sys_capture = self.find_or_create_element(
            "ScanningSystemCapture",
            namespace="mix",
            parent=img_capture,
            after=self._ns("DeviceSource", "mix"),
        )

        if self.img_scanning.scanningsystem:
            s_system = self.img_scanning.scanningsystem[0]
            scanning_hardware = self.find_or_create_element(
                "ScanningSystemHardware", namespace="mix", parent=scan_sys_capture
            )
            if s_system.scanner_model and s_system.scanner_model[0].value:
                scannerModel = self.find_or_create_element(
                    "ScannerModel", namespace="mix", parent=scanning_hardware
                )
                scannerModelName = self.find_or_create_element(
                    "ScannerModelName", namespace="mix", parent=scannerModel
                )
                scannerModelName.text = s_system.scanner_model[0].value
            if s_system.scanner_manufacturer and s_system.scanner_manufacturer[0].value:
                scannerManufacturer = self.find_or_create_element(
                    "ScannerManufacturer", namespace="mix", parent=scanning_hardware
                )
                scannerManufacturer.text = s_system.scanner_manufacturer[0].value

            if self.creation_time:
                datetime_created = self.find_or_create_element(
                    "DateTimeCreated",
                    namespace="mix",
                    parent=img_capture,
                    after=self._ns("ScanningSystemCapture", "mix"),
                )
                datetime_created.text = self.creation_time

            scanning_sys_software = self.find_or_create_element(
                "ScanningSystemSoftware",
                namespace="mix",
                parent=scan_sys_capture,
                after=self._ns("ScanningSystemHardware", "mix"),
            )

            if s_system.capture_software and s_system.capture_software[0].value:
                scanning_software = self.find_or_create_element(
                    "ScanningSoftware", namespace="mix", parent=scanning_sys_software
                )
                scanning_software.text = s_system.capture_software[0].value


class StruLayer(MagMetsConverter):
    def __init__(self, imgs_map, stru, mets_structmap):
        self.imgs_map = imgs_map
        self.stru = stru
        self.structmap = mets_structmap

        self.root_div = self.find_or_create_element("div", parent=self.structmap)

    def convert(self):
        for stru_node in self.stru:
            stru_element = stru_node.element[0]
            stru_start_seqn = int(stru_element.start[0].sequence_number.value)
            stru_end_seqn = int(stru_element.stop[0].sequence_number.value)

            stru_nomenclature = stru_node.nomenclature[0].value

            div = etree.SubElement(self.root_div, self._ns("div"))
            div.attrib["TYPE"] = "section"
            div.attrib["LABEL"] = stru_nomenclature

            for seq_n in range(stru_start_seqn, stru_end_seqn + 1):
                div.append(self._find_page_in_rootdiv(self.imgs_map[seq_n]))

    def _find_page_in_rootdiv(self, page_nomenclature):
        # ritorna il nodo div contenuto nella root della structMap della pagina
        # che ha questa nomenclatura
        for child_div in self.root_div:
            if (child_div.attrib["TYPE"] == "page") and (
                child_div.attrib["LABEL"] == page_nomenclature
            ):
                return child_div

        return None


class MetsHdrBuilder:
    """Build the <metsHdr> element"""

    def build(self, gen, agents_info, fill_element=None):
        if fill_element is None:
            mets_hdr_el = XmlUtils.create_element("metsHdr")
        else:
            mets_hdr_el = fill_element

        mets_hdr_el.attrib["RECORDSTATUS"] = "complete"
        # metto la data di creazione del gen nel metsHdr
        if gen.creation.value:
            # non c'è bisogno di convertire il valore, anche nel mag
            # la data è in formato xsd:dateTime
            mets_hdr_el.attrib["CREATEDATE"] = gen.creation.value

        # metto la data di ultima modifica del gen nel metsHdr
        if gen.last_update.value:
            mets_hdr_el.attrib["LASTMODDATE"] = gen.last_update.value

        for agent_info in agents_info:
            mets_hdr_el.append(self._agent_el(agent_info))

        return mets_hdr_el

    def _agent_el(cls, agent_info):
        el = XmlUtils.create_element("agent")
        el.attrib["ROLE"] = agent_info["role"]
        el.attrib["TYPE"] = agent_info["type"]
        if agent_info.get("otherrole"):
            el.attrib["OTHERROLE"] = agent_info["otherrole"]

        if agent_info.get("id"):
            el.attrib["ID"] = agent_info["id"]

        name_el = XmlUtils.find_or_create_element("name", el)
        name_el.text = agent_info["name"]
        return el


class MODSBuilder:
    """Build the <mdWrap MDTYPE="MODS" element"""

    def build(self, mods_info):
        mdwrap_el = XmlUtils.create_element("mdWrap")
        mdwrap_el.attrib["MDTYPE"] = "MODS"
        xml_data_el = XmlUtils.find_or_create_element("xmlData", parent=mdwrap_el)
        mods_el = XmlUtils.find_or_create_element(
            "mods", namespace="mods", parent=xml_data_el
        )

        for mods_field_info in mods_info:
            el = XmlUtils.create_element(mods_field_info["field"], namespace="mods")
            el.text = mods_field_info["text"]
            if mods_field_info.get("type"):
                el.attrib["type"] = mods_field_info.get("type")
            mods_el.append(el)

        return mdwrap_el


class RightsBuilder:

    """Build the <amdSec> with <rightsMD> element inside"""

    def build(self, rights_info):
        amdsec_el = XmlUtils.create_element("amdSec")
        rightsmd_el = XmlUtils.find_or_create_element("rightsMD", amdsec_el)
        rightsmd_el.attrib["ID"] = rights_info["id"]

        mdwrap_el = XmlUtils.find_or_create_element("mdWrap", rightsmd_el)
        mdwrap_el.attrib["MDTYPE"] = "METSRIGHTS"
        mdwrap_el.attrib["MIMETYPE"] = "text/xml"
        mdwrap_el.attrib["LABEL"] = rights_info["label"]

        xmldata_el = XmlUtils.find_or_create_element("xmlData", mdwrap_el)

        rights_decl_el = XmlUtils.find_or_create_element(
            "RightsDeclarationMD", xmldata_el, namespace="metsrights"
        )
        rights_decl_el.attrib["RIGHTSCATEGORY"] = "COPYRIGHTED"
        rights_holder_el = XmlUtils.find_or_create_element(
            "RightsHolder", rights_decl_el, namespace="metsrights"
        )
        etree.SubElement(
            rights_holder_el, XmlUtils.ns("RightsHolderName", "metsrights")
        ).text = rights_info["rights_holder_name"]
        # etree.SubElement(
        #     rights_holder_el, XmlUtils.ns("RightsHolderDescription", "metsrights")
        # ).text = rights_info["rights_holder_description"]

        # etree.SubElement(
        #     rights_holder_el, XmlUtils.ns("RightsHolderAddress", "metsrights")
        # ).text = rights_info["rights_holder_address"]

        return amdsec_el


def _get_struct_div_resources_container(mets):
    # return the <div> in the structMap containing as children a div for every
    # resource
    struct_map = XmlUtils.find_or_create_element("structMap", parent=mets)
    if not len(struct_map):
        return None

    root_div = struct_map[0]
    if not len(root_div):
        return struct_map
    else:
        return root_div
