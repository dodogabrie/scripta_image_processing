from lxml import etree

from .xmlutils import XmlUtils

FILE_TECH_AMDSEC_ID = "file-tech-amdsec"


def get_file_tech_amdsec(mets):
    return XmlUtils.find_or_create_element(
        "amdSec", mets, attributes={"ID": FILE_TECH_AMDSEC_ID}
    )


def file_element(img, id_, file_seq_n, admid=None):
    """Build <mets:file> element for a resource"""

    fiLe = etree.Element(XmlUtils.ns("file"))

    fiLe.attrib["ID"] = id_

    fiLe.attrib["SEQ"] = file_seq_n

    if img.format and img.format[0].mime and img.format[0].mime[0].value:
        fiLe.attrib["MIMETYPE"] = img.format[0].mime[0].value

    if img.filesize and img.filesize[0].value:
        fiLe.attrib["SIZE"] = img.filesize[0].value

    if img.datetimecreated and img.datetimecreated[0].value:
        fiLe.attrib["CREATED"] = img.datetimecreated[0].value

    if img.md5 and img.md5[0].value:
        fiLe.attrib["CHECKSUMTYPE"] = "MD5"
        fiLe.attrib["CHECKSUM"] = img.md5[0].value

    if admid:
        fiLe.attrib["ADMID"] = admid

    if img.file and img.file[0].href:
        f_loc = etree.SubElement(fiLe, XmlUtils.ns("FLocat"))
        f_loc.attrib["LOCTYPE"] = "URL"
        f_loc.attrib[XmlUtils.ns("href", "xlink")] = img.file[0].href.value

    return fiLe


def fileptr_element(id_):
    el = etree.Element(XmlUtils.ns("fptr"))
    el.attrib["FILEID"] = id_
    return el


def tech_md_wrapper(id_, mdtype):
    """Return a <mets:tecthMD> element with mdWrap/xmlData structure"""

    el = XmlUtils.create_element("techMD")
    el.attrib["ID"] = id_
    mdwrap = etree.SubElement(el, XmlUtils.ns("mdWrap"))
    mdwrap.attrib["MDTYPE"] = mdtype
    etree.SubElement(mdwrap, XmlUtils.ns("xmlData"))

    return el


class FileGroups:
    """Management of mets <fileGrp>"""

    def __init__(self, mets):
        self._mets = mets

    def find(self, group_id):
        found = XmlUtils.xpath(
            self._mets, f'mets:fileSec/mets:fileGrp[@ID="{group_id}"]'
        )
        if found:
            return found[0]
        return None

    def create(self, group_id):
        file_sec = XmlUtils.find_or_create_element(
            "fileSec", parent=self._mets, after=XmlUtils.ns("amdSec")
        )
        file_grp = etree.SubElement(file_sec, XmlUtils.ns("fileGrp"))
        file_grp.attrib["ID"] = group_id
        return file_grp

    def find_or_create(self, group_id):
        grp = self.find(group_id)
        if grp is not None:
            return grp
        return self.create(group_id)


def message_digest_el(proxy, namespace):
    el = XmlUtils.create_element("messageDigest", namespace)

    el.append(
        XmlUtils.element_with_text(
            "messageDigestDatetime", namespace, proxy.datetimecreated[0].value
        )
    )
    el.append(XmlUtils.element_with_text("messageDigestAlgorithm", namespace, "md5"))
    el.append(
        XmlUtils.element_with_text("messageDigest", namespace, proxy.md5[0].value)
    )
    return el
