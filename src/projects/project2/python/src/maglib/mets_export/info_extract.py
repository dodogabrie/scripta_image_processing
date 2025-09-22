import re


class AgentsInfoConfigReader:
    """Read info for metsHdrs agents from a ConfigParser

    The ini for the ConfigParser must a list of agent:* sections with
    the following format:

    [agent:0]
    role = creator
    type = organization
    name = SCABEC/Regione Campania
    otherrole =                     # optional
    id =                            # optional

    """

    def read(self, cfg_parser):
        """Return a list of dicts each representing an agent"""

        agents = []

        for agent_section_name in self._get_agent_sections(cfg_parser):
            agent_section = cfg_parser[agent_section_name]
            agents.append(self._parse_agent_section(agent_section))

        return agents

    @classmethod
    def _get_agent_sections(cls, cfg_parser):
        found_sections = []
        for section in cfg_parser.sections():
            m = re.match(r"^agent:(\d+)$", section)
            if not m:
                continue

            found_sections.append((int(m.group(1)), section))

        found_sections.sort()
        return [sec[1] for sec in found_sections]

    @classmethod
    def _parse_agent_section(cls, agent_section):
        agent = {k: agent_section[k] for k in ("role", "type", "name")}
        agent["otherrole"] = agent_section.get("otherrole")
        agent["id"] = agent_section.get("id")
        return agent


class MODSMappingReader:
    """Read MODS information from metadigit using a mapping object

    Currently mapping object can have entries like:
    'identifier': 'identifier'
    'identifier_cont': 'library'

    With the meaning "extract mods:identifier from dc language"
    and "extract mods:identifier of type cont from library".

    """

    def __init__(self, mapping):
        self._mapping = mapping

    def read(self, bib):

        info = []
        for mods_spec, mag_spec in self._mapping.items():
            entry_remap = self._remap_entry(mods_spec, mag_spec, bib)
            if entry_remap is not None:
                info.append(entry_remap)
        return info

    @classmethod
    def _remap_entry(cls, mod_spec, mag_spec, bib):
        m = re.match("^(?P<tag>[a-zA-Z]+)(?:_(?P<type>.+))?$", mod_spec)
        if not m:
            return None

        mag_value = cls._extract_from_mag(mag_spec, bib)

        info = {"text": mag_value, "field": m.group(1)}
        if m.group(2):
            info["type"] = m.group(2)
        return info

    @classmethod
    def _extract_from_mag(cls, mag_spec, bib):
        if mag_spec in ("library", "shelfmark"):
            holdings = bib.holdings[0]
            return getattr(holdings, mag_spec)[0].value
        return getattr(bib, mag_spec)[0].value
