from .base import (
    FileGroups,
    file_element,
    get_file_tech_amdsec,
    message_digest_el,
    tech_md_wrapper,
)
from .xmlutils import XmlUtils


def add_video(
    mets, video, group_name_template="fileGrp{index:02d}", group_name_from_format=True
):
    created = []
    seq_n = int(video.sequence_number[0].value)

    for i, proxy in enumerate(video.proxies):
        group_id = None
        if group_name_from_format:
            group_id = _proxy_group_id(proxy)
        if group_id is None:
            group_id = group_name_template.format(index=i + 1)

        file_id = f"f_{group_id}_{seq_n:05d}"
        tech_md_id = f"{file_id}_techMD"
        tech_md_el = tech_md_wrapper(tech_md_id, "LC-AV")

        mdwrap_el = tech_md_el[0][0]
        mdwrap_el.append(video_md(proxy))

        file_el = file_element(proxy, file_id, str(seq_n), tech_md_id)

        group = FileGroups(mets).find_or_create(group_id)
        use = {0: "master", 1: "alta risoluzione"}.get(i)
        if use:
            group.attrib["USE"] = use

        group.append(file_el)
        amd_sec = get_file_tech_amdsec(mets)
        amd_sec.append(tech_md_el)

        created.append(file_el)

    return created


def video_md(video_proxy):
    """Return the VIDEOMD element for a mag video proxy element"""

    videomd = _element("VIDEOMD")
    videomd.attrib["ANALOGDIGITALFLAG"] = "FileDigital"

    videomd.append(_file_data_el(video_proxy))
    videomd.append(_video_info_el(video_proxy))

    return videomd


def _file_data_el(proxy):
    el = _element("fileData")

    if proxy.video_dimensions and proxy.video_dimensions[0].duration:
        duration = proxy.video_dimensions[0].duration[0].value
        el.append(_element_with_text("duration", duration))

    el.append(message_digest_el(proxy, "videoMD"))

    if proxy.format and (proxy.format[0].name or proxy.format[0].mime):
        format_el = _element("format")
        if proxy.format[0].name:
            format_el.append(_element_with_text("name", proxy.format[0].name[0].value))
        if proxy.format[0].mime:
            format_el.append(
                _element_with_text("mimetype", proxy.format[0].mime[0].value)
            )
        el.append(format_el)

    # if proxy.format and proxy.format[0].name:
    #     compression_el = _element("compression")
    #     compression_el.append(
    #         _element_with_text("codecName", proxy.format[0].name[0].value)
    #     )
    #     el.append(compression_el)

    return el


def _video_info_el(proxy):
    el = _element("videoInfo")

    if proxy.video_metrics:
        video_metrics = proxy.video_metrics[0]
    else:
        video_metrics = None

    if video_metrics:
        if video_metrics.aspectratio:
            aspect_ratio = video_metrics.aspectratio[0].value
            el.append(_element_with_text("aspectRatio", aspect_ratio))

        if video_metrics.videosize:
            try:
                width, height = video_metrics.videosize[0].value.split("x")
            except ValueError:
                pass
            else:
                dimension_el = _element("dimensions")
                dimension_el.attrib["WIDTH"] = width
                dimension_el.attrib["HEIGHT"] = height
                el.append(dimension_el)

    if proxy.video_dimensions and proxy.video_dimensions[0].duration:
        duration = proxy.video_dimensions[0].duration[0].value
        el.append(_element_with_text("duration", duration))

    if video_metrics:
        if video_metrics.framerate:
            framerate = video_metrics.framerate[0].value
            frame_el = _element("frame")
            framerate_el = _element_with_text("frameRate", framerate)
            frame_el.append(framerate_el)
            el.append(frame_el)

    return el


def _proxy_group_id(proxy):
    try:
        format_name = proxy.format[0].name[0].value
    except IndexError:
        format_name = None
    if format_name:
        return f"video_{format_name.lower()}"
    return None


def _element(tag):
    return XmlUtils.create_element(tag, "videoMD")


def _element_with_text(tag, text):
    el = _element(tag)
    el.text = text
    return el
