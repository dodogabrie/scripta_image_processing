from .base import (
    FileGroups,
    file_element,
    get_file_tech_amdsec,
    message_digest_el,
    tech_md_wrapper,
)
from .xmlutils import XmlUtils


def add_audio(mets, audio):

    created = []

    seq_n = int(audio.sequence_number[0].value)

    for i, proxy in enumerate(audio.proxies):
        group_id = _proxy_group_id(proxy) or f"audio_grp{i}"
        file_id = f"f_{group_id}_{seq_n:05d}"

        tech_md_id = f"{file_id}_techMD"
        tech_md_el = tech_md_wrapper(tech_md_id, "LC-AV")
        mdwrap_el = tech_md_el[0][0]
        mdwrap_el.append(audio_md(proxy))

        file_el = file_element(proxy, file_id, str(seq_n), tech_md_id)

        group = FileGroups(mets).find_or_create(group_id)

        group.append(file_el)
        amd_sec = get_file_tech_amdsec(mets)
        amd_sec.append(tech_md_el)

        created.append(file_el)

    return created


def audio_md(audio_proxy):
    """Return the AUDIOMD element for a mag audio proxy element"""

    audiomd = _element("AUDIOMD")
    audiomd.attrib["ANALOGDIGITALFLAG"] = "FileDigital"

    audiomd.append(_file_data_el(audio_proxy))
    audiomd.append(_audio_info_el(audio_proxy))

    return audiomd


def _proxy_group_id(proxy):
    try:
        format_name = proxy.format[0].name[0].value
    except IndexError:
        format_name = None
    if format_name:
        return f"audio_{format_name.lower()}"
    return None


def _file_data_el(proxy):
    el = _element("fileData")

    el.append(_element_with_text("audioDataEncoding", "PCM"))

    if proxy.audio_metrics:
        metrics = proxy.audio_metrics[0]
    else:
        metrics = None

    if metrics is not None and metrics.bitpersample:
        bitpersample = metrics.bitpersample[0].value
        el.append(_element_with_text("bitsPerSample", bitpersample))

    el.append(message_digest_el(proxy, "audioMD"))

    if proxy.format:
        format_ = proxy.format[0]
        if format_.name:
            el.append(_element_with_text("formatName", format_.name[0].value))

    if metrics is not None and metrics.samplingfrequency:
        samplingfrequency = metrics.samplingfrequency[0].value
        el.append(_element_with_text("samplingFrequency", samplingfrequency))

    el.append(_element_with_text("use", "Master"))

    return el


def _audio_info_el(proxy):
    el = _element("audioInfo")

    if proxy.audio_dimensions and proxy.audio_dimensions[0].duration:
        duration = proxy.audio_dimensions[0].duration[0].value
        el.append(_element_with_text("duration", duration))

    if proxy.format and proxy.format[0].channel_configuration:
        ch_conf = proxy.format[0].channel_configuration[0].value
        channels = {
            "Mono": 1,
            "Dual mono": 1,
            "Joint stereo": 2,
            "Stereo": 2,
            "2 ch": 2,
            "4 ch": 4,
            "5.1 ch": 6,
            "6.1 ch": 6,
        }[ch_conf]
        el.append(_element_with_text("numChannels", str(channels)))

        el.append(_element_with_text("soundField", ch_conf))

    return el


def _element(tag):
    return XmlUtils.create_element(tag, "audioMD")


def _element_with_text(tag, text):
    el = _element(tag)
    el.text = text
    return el
